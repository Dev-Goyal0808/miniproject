#!/usr/bin/env python3
"""
v2 - one final pipeline, selected by NESTED grouped CV, trained on original + augmented windows.

What changed vs v1 (all driven by the v1 diagnostics: sensitivity 36%, 2:1 imbalance,
augmentation hurt, 496 features for 90 recordings):
  1. Compact, robust features (~115): GWST pooled into 1 Hz bands (log-L1 + entropy),
     plus relative band powers, spectral entropy/edge, Hjorth, kurtosis, line length, etc.
  2. Model + decision threshold are chosen on INNER grouped folds of the training data only
     (ExtraTrees / HistGB / RBF-SVM / LogReg), optimising balanced accuracy -> fixes low sensitivity.
  3. Gentler augmentation (time shift, sign flip, low noise; NO gain change, which destroys amplitude cues).
     Augmented copies are only used when their source window is in the training fold.
  4. Two evaluations:
       A) natural 2:1 data (all recordings) -> balanced accuracy is the headline
       B) PAPER-MATCHED: 30 epilepsy vs 30 randomly drawn healthy recordings, repeated draws
          -> directly comparable to the paper's balanced 540-frame setup.
All splits are grouped by recording (or subject with --subject-regex). No test-fold leakage.
"""
import argparse, json, re, sys, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt, welch
from scipy.stats import kurtosis, skew
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score, recall_score, balanced_accuracy_score, f1_score, cohen_kappa_score

warnings.filterwarnings("ignore")
FS = 512
PAPER = {"cv10_acc": 74.44, "holdout_acc": 90.74}

# ----------------------------------------------------------------- data ----
def read_signal(path):
    df = pd.read_csv(path, header=None, dtype=str, skip_blank_lines=True)
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    return df.iloc[:, 0].dropna().to_numpy(float)

def infer_label(path):
    s = "/".join(path.parts).lower()
    if re.search(r"epilep|seiz|patient", s): return 1
    if re.search(r"health|control|normal", s): return 0
    return None

def load_recordings(data_dir, labels_csv=None, subject_regex=None, n_samples=10240):
    data_dir = Path(data_dir)
    lab_map = pd.read_csv(labels_csv).set_index("file")["label"].to_dict() if labels_csv else None
    recs, bad = [], []
    for f in sorted(data_dir.rglob("*.csv")):
        y = lab_map.get(f.name) if lab_map is not None else infer_label(f)
        if y is None: bad.append(str(f)); continue
        x = read_signal(f)[:n_samples]
        if len(x) < n_samples // 2: continue
        uid = str(f.relative_to(data_dir).with_suffix(""))
        grp = uid
        if subject_regex:
            m = re.search(subject_regex, f.name)
            grp = f"{int(y)}:{m.group(1)}" if m else uid
        recs.append((uid, grp, int(y), x))
    if bad: sys.exit("Cannot infer labels for:\n  " + "\n  ".join(bad[:10]) + "\nUse --labels labels.csv (file,label).")
    if not recs: sys.exit("No CSV recordings found.")
    return recs

def bandpass(x, lo=0.5, hi=50.0):
    return sosfiltfilt(butter(4, [lo, hi], btype="band", fs=FS, output="sos"), x - np.mean(x))

def make_windows(recs, win_s=5.0, stride_s=2.5):
    W, y, rid, grp = [], [], [], []
    L, S = int(win_s * FS), int(stride_s * FS)
    for i, (_, g, lab, x) in enumerate(recs):
        x = bandpass(x)
        for s in range(0, len(x) - L + 1, S):
            W.append(x[s:s + L]); y.append(lab); rid.append(i); grp.append(g)
    return np.asarray(W), np.asarray(y), np.asarray(rid), np.asarray(grp)

# ------------------------------------------------------------- features ----
def gwst_pooled(w, fmin=0.5, fmax=50.0, nbins=10):
    N = len(w)
    X = np.fft.fft(w) / N
    ks = np.arange(int(np.ceil(fmin * N / FS)), int(np.floor(fmax * N / FS)) + 1)
    al = np.fft.fftfreq(N, 1.0 / N).astype(int)
    A = np.abs(np.fft.ifft(X[(ks[:, None] + al[None, :]) % N] *
                           np.exp(-2 * np.pi ** 2 * al[None, :] ** 2 / ks[:, None] ** 2), axis=1))
    logl1 = np.log(A.sum(1) + 1e-9)
    lo, hi = A.min(1, keepdims=True), A.max(1, keepdims=True)
    idx = np.clip(((A - lo) / (hi - lo + 1e-12) * nbins).astype(int), 0, nbins - 1)
    p = np.stack([(idx == b).mean(1) for b in range(nbins)], 1)
    ent = -(p * np.log2(p + 1e-12)).sum(1)
    band = np.clip(np.floor(ks * FS / N - 0.5).astype(int), 0, 49)
    cnt = np.bincount(band, minlength=50).clip(min=1)
    return np.concatenate([np.bincount(band, logl1, 50) / cnt, np.bincount(band, ent, 50) / cnt])

def stat_features(w):
    f, P = welch(w, FS, nperseg=1024)
    m = (f >= 0.5) & (f <= 50); f, P = f[m], P[m]
    tot = P.sum() + 1e-12; pn = P / tot
    rel = [P[(f >= a) & (f < b)].sum() / tot for a, b in [(0.5, 4), (4, 8), (8, 13), (13, 30), (30, 50.1)]]
    sent = -(pn * np.log2(pn + 1e-12)).sum()
    sef = f[min(np.searchsorted(np.cumsum(pn), 0.95), len(f) - 1)]
    d1, d2 = np.diff(w), np.diff(w, 2)
    var = np.var(w) + 1e-12
    mob = np.sqrt(np.var(d1) / var); comp = np.sqrt(np.var(d2) / (np.var(d1) + 1e-12)) / (mob + 1e-12)
    return np.array(rel + [np.log(tot), sent, sef, np.log(var), mob, comp, kurtosis(w), skew(w),
                           np.mean(np.abs(d1)) / np.sqrt(var), np.mean(np.diff(np.sign(w)) != 0),
                           np.ptp(w) / np.sqrt(var)])

def featurize(W):
    return np.vstack([np.concatenate([gwst_pooled(w), stat_features(w)]) for w in W])

# ---------------------------------------------------------- augmentation ----
def augment(w, rng):
    o = np.roll(w, int(rng.integers(-FS // 2, FS // 2)))
    if rng.random() < 0.5: o = -o
    snr = rng.uniform(25, 35)
    return o + rng.normal(0, np.std(o) * 10 ** (-snr / 20), o.shape)

def build_aug(W, n_copies, seed=12345):
    rng = np.random.default_rng(seed); src, AW = [], []
    for i, w in enumerate(W):
        for _ in range(n_copies): AW.append(augment(w, rng)); src.append(i)
    return featurize(np.asarray(AW)), np.asarray(src)

# --------------------------------------------------------------- models ----
def candidates(seed):
    def hgb():
        try: return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                                   l2_regularization=1.0, class_weight="balanced", random_state=seed)
        except TypeError: return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                                                l2_regularization=1.0, random_state=seed)
    return {
        "extra_trees": lambda: ExtraTreesClassifier(400, min_samples_leaf=2, class_weight="balanced_subsample",
                                                    n_jobs=-1, random_state=seed),
        "hist_gb": hgb,
        "rbf_svm": lambda: make_pipeline(StandardScaler(), SVC(C=3, gamma="scale", class_weight="balanced",
                                                               probability=True, random_state=seed)),
        "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.1, class_weight="balanced", max_iter=3000)),
    }

THRS = np.linspace(0.2, 0.8, 25)

def train_set(F, FA, srcA, y, idx, use_aug):
    if not use_aug: return F[idx], y[idx]
    keep = np.isin(srcA, idx)                                   # copies of TRAIN windows only
    return np.vstack([F[idx], FA[keep]]), np.concatenate([y[idx], y[srcA[keep]]])

def select_and_fit(F, FA, srcA, y, grp, idx, seed, use_aug):
    cands = candidates(seed)
    oof = {n: np.zeros(len(idx)) for n in cands}
    inner = StratifiedGroupKFold(3, shuffle=True, random_state=seed)
    for itr, ite in inner.split(idx, y[idx], grp[idx]):
        X, yy = train_set(F, FA, srcA, y, idx[itr], use_aug)
        for n, mk in cands.items():
            oof[n][ite] = mk().fit(X, yy).predict_proba(F[idx[ite]])[:, 1]
    best = (-1, None, 0.5)
    for n in cands:
        for t in THRS:
            s = balanced_accuracy_score(y[idx], (oof[n] >= t).astype(int))
            if s > best[0]: best = (s, n, t)
    score, name, thr = best
    X, yy = train_set(F, FA, srcA, y, idx, use_aug)
    return cands[name]().fit(X, yy), float(thr), name, float(score)

# ------------------------------------------------------------ evaluation ----
def metrics(y, p):
    tn = np.sum((y == 0) & (p == 0)); fp = np.sum((y == 0) & (p == 1))
    return dict(acc=100 * accuracy_score(y, p), bal_acc=100 * balanced_accuracy_score(y, p),
                sen=100 * recall_score(y, p, zero_division=0), spe=100 * tn / max(tn + fp, 1),
                f1=f1_score(y, p, zero_division=0), kappa=cohen_kappa_score(y, p))

def run_cv(F, FA, srcA, y, grp, rid, sub, seed, folds, use_aug):
    pred = np.zeros(len(y), int); fold_acc, chosen = [], []
    cv = StratifiedGroupKFold(folds, shuffle=True, random_state=seed)
    for tr, te in cv.split(sub, y[sub], grp[sub]):
        m, thr, name, _ = select_and_fit(F, FA, srcA, y, grp, sub[tr], seed, use_aug)
        p = (m.predict_proba(F[sub[te]])[:, 1] >= thr).astype(int)
        pred[sub[te]] = p; fold_acc.append(100 * accuracy_score(y[sub[te]], p)); chosen.append(name)
    yw, pw = y[sub], pred[sub]
    ids = np.unique(rid[sub])
    yr = np.array([y[rid == i][0] for i in ids]); pr = np.array([pred[rid == i].mean() >= 0.5 for i in ids]).astype(int)
    return dict(window=metrics(yw, pw), recording=metrics(yr, pr), fold_acc=fold_acc, chosen=chosen)

def agg(runs):
    f = lambda lvl: {k: float(np.mean([r[lvl][k] for r in runs])) for k in runs[0][lvl]}
    fa = [a for r in runs for a in r["fold_acc"]]
    ch = [c for r in runs for c in r["chosen"]]
    return dict(window=f("window"), recording=f("recording"), fold_acc_mean=float(np.mean(fa)),
                fold_acc_std=float(np.std(fa)), chosen={n: ch.count(n) for n in set(ch)},
                run_acc_std=float(np.std([r["window"]["acc"] for r in runs])))

# ----------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--labels"); ap.add_argument("--subject-regex")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--folds", type=int, default=10)
    ap.add_argument("--draws", type=int, default=5, help="random 30-vs-30 draws for the paper-matched protocol")
    ap.add_argument("--aug-copies", type=int, default=3)
    ap.add_argument("--stride", type=float, default=2.5)
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default="results_v2.json")
    a = ap.parse_args()
    if a.quick: a.seeds, a.folds, a.draws, a.aug_copies = [0], 5, 2, 2

    t0 = time.time()
    recs = load_recordings(a.data_dir, a.labels, a.subject_regex)
    W, y, rid, grp = make_windows(recs, 5.0, a.stride)
    nE = len({r for r, l in zip(rid, y) if l == 1}); nH = len(recs) - nE
    print(f"{len(recs)} recordings ({nE} epilepsy / {nH} healthy), {len(W)} windows; "
          f"majority-class baseline = {100*max(nE,nH)/len(recs):.1f}%")
    cache = Path(f"feat_cache_{len(W)}_{a.aug_copies}_{a.stride}.npz")
    if cache.exists():
        z = np.load(cache); F, FA, srcA = z["F"], z["FA"], z["srcA"]; print("loaded cached features")
    else:
        F = featurize(W); FA, srcA = build_aug(W, a.aug_copies); np.savez(cache, F=F, FA=FA, srcA=srcA)
    print(f"features {F.shape}, augmented {FA.shape} ({time.time()-t0:.0f}s)")

    res, modes = {}, [("aug", True)] + ([("noaug", False)] if a.ablation else [])
    allw = np.arange(len(y))
    for name, use_aug in modes:
        # A) natural class ratio, all recordings
        A = agg([run_cv(F, FA, srcA, y, grp, rid, allw, s, a.folds, use_aug) for s in a.seeds])
        # B) paper-matched: all epilepsy + equal number of randomly drawn healthy recordings
        epi = np.array([i for i in range(len(recs)) if y[rid == i][0] == 1])
        hea = np.array([i for i in range(len(recs)) if y[rid == i][0] == 0])
        runs = []
        for d in range(a.draws):
            rng = np.random.default_rng(100 + d)
            keep = np.concatenate([epi, rng.choice(hea, size=len(epi), replace=False)])
            sub = np.where(np.isin(rid, keep))[0]
            runs.append(run_cv(F, FA, srcA, y, grp, rid, sub, a.seeds[0] + d, a.folds, use_aug))
        B = agg(runs)
        res[name] = {"A_natural": A, "B_paper_matched": B}
        print(f"\n[{name}] A) natural ratio  : bal_acc {A['window']['bal_acc']:.2f} | acc {A['window']['acc']:.2f} | "
              f"sen {A['window']['sen']:.2f} | spe {A['window']['spe']:.2f} | recording-level bal_acc {A['recording']['bal_acc']:.2f}")
        print(f"[{name}] B) 30v30 matched : acc {B['window']['acc']:.2f} +/- {B['fold_acc_std']:.2f} (fold std) | "
              f"sen {B['window']['sen']:.2f} | spe {B['window']['spe']:.2f} | recording-level acc {B['recording']['acc']:.2f}")
        print(f"[{name}] models chosen (A): {A['chosen']}  (B): {B['chosen']}")

    B = res["aug"]["B_paper_matched"]; d = B["window"]["acc"] - PAPER["cv10_acc"]
    print("\n=== VERDICT vs base paper (10-fold CV, balanced 30v30, 74.44%) ===")
    print(f"this model: {B['window']['acc']:.2f}%  ({d:+.2f} pts) -> {'ABOVE' if d > 0 else 'NOT above'}"
          f"{'' if abs(d) > B['fold_acc_std'] else '  [within fold std: not statistically distinguishable]'}")
    print("The paper's 90.74% hold-out is likely a random frame split (leaky); it is not a fair target for grouped evaluation.")
    res["paper"] = PAPER
    Path(a.out).write_text(json.dumps(res, indent=2)); print(f"Saved {a.out} ({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()
