#!/usr/bin/env python3
"""
Single fixed model (Random Forest) on Gaussian-window Stockwell (GWST) L1-norm +
histogram-entropy features, trained on ORIGINAL + AUGMENTED 5 s windows.
Benchmarked against Dash et al., Biomed. Signal Process. Control 100 (2025) 107041.

Leakage controls (the reason this number is trustworthy):
  * every split is GROUPED BY RECORDING (or by subject if --subject-regex is given),
    so no window of a test recording ever appears in training;
  * augmented copies are made per window, and only copies whose SOURCE window is
    in the training fold are used for training; test folds are never augmented;
  * hyper-parameters are fixed in advance (no tuning on test folds).

Usage:
  python epilepsy_gwst_rf_final.py --data-dir ./eeg_csvs
  python epilepsy_gwst_rf_final.py --data-dir ./eeg_csvs --labels labels.csv   # columns: file,label(0/1)
Labels are otherwise inferred from path text: epilep|seiz|patient -> 1 ; health|control|normal -> 0.
"""
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold, GroupShuffleSplit
from sklearn.metrics import (accuracy_score, recall_score, balanced_accuracy_score,
                             f1_score, cohen_kappa_score)

FS = 512                      # Hz (Neurosky MindWave, per paper)
PAPER = {"cv10_acc": 74.44,   # multi-layer LSTM, 10-fold CV (paper's fair headline)
         "holdout_acc": 90.74}  # RF, random hold-out (likely frame-level split)

# ----------------------------------------------------------------- data ----
def read_signal(path):
    """Robust CSV read: tolerates trailing commas, headers, 10,241 vs 10,240 rows."""
    df = pd.read_csv(path, header=None, dtype=str, skip_blank_lines=True)
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    if df.shape[1] == 0:
        raise ValueError(f"no numeric column in {path}")
    x = df.iloc[:, 0].dropna().to_numpy(float)
    return x

def infer_label(path):
    s = "/".join(path.parts).lower()
    if re.search(r"epilep|seiz|patient", s):
        return 1
    if re.search(r"health|control|normal", s):
        return 0
    return None

def load_recordings(data_dir, labels_csv=None, subject_regex=None, n_samples=10240):
    files = sorted(Path(data_dir).rglob("*.csv"))
    lab_map = None
    if labels_csv:
        lab_map = pd.read_csv(labels_csv).set_index("file")["label"].to_dict()
    recs, bad = [], []
    for f in files:
        if labels_csv and f.name not in lab_map and f.name == Path(labels_csv).name:
            continue
        y = lab_map.get(f.name) if lab_map is not None else infer_label(f)
        if y is None:
            bad.append(str(f)); continue
        x = read_signal(f)
        if len(x) > n_samples:
            x = x[:n_samples]                  # drop the extra 10,241st row
        if len(x) < n_samples // 2:
            print(f"[skip] too short: {f}"); continue
        uid = str(f.relative_to(data_dir).with_suffix(""))   # unique per file, even across class folders
        group = uid
        if subject_regex:
            m = re.search(subject_regex, f.name)
            group = f"{int(y)}:{m.group(1)}" if m else uid
        recs.append((uid, group, int(y), x))
    if bad:
        sys.exit("Could not infer labels for:\n  " + "\n  ".join(bad[:10]) +
                 "\nProvide --labels labels.csv (columns: file,label).")
    if not recs:
        sys.exit("No CSV recordings found.")
    return recs

def bandpass(x, lo=0.5, hi=50.0, fs=FS):
    sos = butter(4, [lo, hi], btype="band", fs=fs, output="sos")
    return sosfiltfilt(sos, x - np.mean(x))

def make_windows(recs, win_s=5.0, stride_s=2.5):
    W, y, rid, grp = [], [], [], []
    L, S = int(win_s * FS), int(stride_s * FS)
    for i, (name, group, lab, x) in enumerate(recs):
        x = bandpass(x)
        for s in range(0, len(x) - L + 1, S):
            W.append(x[s:s + L]); y.append(lab); rid.append(i); grp.append(group)
    return np.asarray(W), np.asarray(y), np.asarray(rid), np.asarray(grp)

# ------------------------------------------------------------- features ----
def gwst_features(w, fs=FS, fmin=0.5, fmax=50.0, nbins=10):
    """Gaussian-window Stockwell transform -> per-frequency [L1 norm, histogram entropy]."""
    N = len(w)
    X = np.fft.fft(w) / N
    ks = np.arange(max(1, int(np.ceil(fmin * N / fs))), int(np.floor(fmax * N / fs)) + 1)
    alpha = np.fft.fftfreq(N, 1.0 / N).astype(int)
    Xs = X[(ks[:, None] + alpha[None, :]) % N]
    G = np.exp(-2 * np.pi ** 2 * alpha[None, :] ** 2 / ks[:, None] ** 2)
    A = np.abs(np.fft.ifft(Xs * G, axis=1))                 # (n_freq, N)
    l1 = A.sum(1)
    lo, hi = A.min(1, keepdims=True), A.max(1, keepdims=True)
    idx = np.clip(((A - lo) / (hi - lo + 1e-12) * nbins).astype(int), 0, nbins - 1)
    p = np.stack([(idx == b).mean(1) for b in range(nbins)], 1)
    ent = -(p * np.log2(p + 1e-12)).sum(1)
    return np.concatenate([l1, ent])

def featurize(W):
    return np.vstack([gwst_features(w) for w in W])

# ---------------------------------------------------------- augmentation ----
def augment(w, rng):
    o = np.roll(w, int(rng.integers(-FS // 2, FS // 2)))      # circular time shift (<=0.5 s)
    o = o * rng.uniform(0.9, 1.1)                             # mild gain change
    snr = rng.uniform(12, 25)                                 # additive white noise
    o = o + rng.normal(0, np.std(o) * 10 ** (-snr / 20), o.shape)
    return o

def build_aug(W, n_copies, seed):
    rng = np.random.default_rng(seed)
    src, AW = [], []
    for i, w in enumerate(W):
        for _ in range(n_copies):
            AW.append(augment(w, rng)); src.append(i)
    return featurize(np.asarray(AW)), np.asarray(src)

# ---------------------------------------------------------------- model ----
def new_model(seed):
    # ONE fixed model; settings chosen a priori, never tuned on test data.
    return RandomForestClassifier(n_estimators=500, max_features="sqrt", min_samples_leaf=1,
                                  class_weight="balanced_subsample", n_jobs=-1, random_state=seed)

def metrics(y, p):
    tn = np.sum((y == 0) & (p == 0)); fp = np.sum((y == 0) & (p == 1))
    return dict(acc=100 * accuracy_score(y, p), sen=100 * recall_score(y, p, zero_division=0),
                spe=100 * tn / max(tn + fp, 1), bal_acc=100 * balanced_accuracy_score(y, p),
                f1=f1_score(y, p, zero_division=0), kappa=cohen_kappa_score(y, p))

def fit_predict(F, FA, srcA, y, tr, te, seed, use_aug=True):
    Xtr, ytr = F[tr], y[tr]
    if use_aug:
        keep = np.isin(srcA, tr)                               # only copies of TRAIN windows
        Xtr = np.vstack([Xtr, FA[keep]]); ytr = np.concatenate([ytr, y[srcA[keep]]])
    m = new_model(seed).fit(Xtr, ytr)
    return m.predict_proba(F[te])[:, 1]

def rec_level(prob, rid_te, y_te):
    ids = np.unique(rid_te)
    pr = np.array([prob[rid_te == i].mean() > 0.5 for i in ids]).astype(int)
    yr = np.array([y_te[rid_te == i][0] for i in ids])
    return yr, pr

# ----------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--labels"); ap.add_argument("--subject-regex")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--folds", type=int, default=10)
    ap.add_argument("--aug-copies", type=int, default=3)
    ap.add_argument("--stride", type=float, default=2.5)
    ap.add_argument("--ablation", action="store_true", help="also run without augmentation")
    ap.add_argument("--out", default="results_gwst_rf.json")
    a = ap.parse_args()

    t0 = time.time()
    recs = load_recordings(a.data_dir, a.labels, a.subject_regex)
    W, y, rid, grp = make_windows(recs, 5.0, a.stride)
    n_groups = len(np.unique(grp))
    print(f"{len(recs)} recordings, {n_groups} groups, {len(W)} windows "
          f"(epilepsy={int(y.sum())}, healthy={int((y==0).sum())})")
    if n_groups == len(recs):
        print("NOTE: groups = recordings (no participant IDs). Results are recording-independent, "
              "NOT participant-independent.")
    F = featurize(W)
    FA, srcA = build_aug(W, a.aug_copies, seed=12345)
    print(f"features {F.shape}, augmented {FA.shape}  ({time.time()-t0:.0f}s)")

    res = {"cv": {}, "holdout": {}}
    modes = [("aug", True)] + ([("noaug", False)] if a.ablation else [])
    for name, use_aug in modes:
        folds_acc, win_pool, rec_pool = [], [], []
        for s in a.seeds:
            cv = StratifiedGroupKFold(a.folds, shuffle=True, random_state=s)
            oof = np.zeros(len(y))
            for tr, te in cv.split(F, y, grp):
                pr = fit_predict(F, FA, srcA, y, tr, te, s, use_aug)
                oof[te] = pr
                folds_acc.append(100 * accuracy_score(y[te], pr > 0.5))
            win_pool.append(metrics(y, (oof > 0.5).astype(int)))
            yr, pr_r = rec_level(oof, rid, y); rec_pool.append(metrics(yr, pr_r))
        res["cv"][name] = dict(
            fold_acc_mean=float(np.mean(folds_acc)), fold_acc_std=float(np.std(folds_acc)),
            window_pooled={k: float(np.mean([m[k] for m in win_pool])) for k in win_pool[0]},
            recording_pooled={k: float(np.mean([m[k] for m in rec_pool])) for k in rec_pool[0]})
        hs = []
        for s in a.seeds:
            tr, te = next(GroupShuffleSplit(1, test_size=0.2, random_state=s).split(F, y, grp))
            pr = fit_predict(F, FA, srcA, y, tr, te, s, use_aug)
            hs.append(metrics(y[te], (pr > 0.5).astype(int))["acc"])
        res["holdout"][name] = dict(acc_mean=float(np.mean(hs)), acc_std=float(np.std(hs)))

    r = res["cv"]["aug"]
    print("\n=== RESULTS (grouped, leak-free) ===")
    print(f"{a.folds}-fold CV  window-level fold acc : {r['fold_acc_mean']:.2f} +/- {r['fold_acc_std']:.2f}")
    print(f"{a.folds}-fold CV  pooled window metrics  : {json.dumps({k: round(v,3) for k,v in r['window_pooled'].items()})}")
    print(f"{a.folds}-fold CV  recording-level metrics: {json.dumps({k: round(v,3) for k,v in r['recording_pooled'].items()})}")
    h = res["holdout"]["aug"]
    print(f"Grouped 80/20 hold-out acc            : {h['acc_mean']:.2f} +/- {h['acc_std']:.2f}")
    if a.ablation:
        print(f"[ablation] no-aug CV acc {res['cv']['noaug']['fold_acc_mean']:.2f}, "
              f"hold-out {res['holdout']['noaug']['acc_mean']:.2f}")

    print("\n=== COMPARISON WITH BASE PAPER ===")
    d_cv = r["fold_acc_mean"] - PAPER["cv10_acc"]
    d_ho = h["acc_mean"] - PAPER["holdout_acc"]
    print(f"vs 10-fold CV 74.44% : {d_cv:+.2f} pts -> {'ABOVE' if d_cv > 0 else 'NOT above'}"
          f"{'' if abs(d_cv) > r['fold_acc_std'] else ' (within fold std: not a significant difference)'}")
    print(f"vs hold-out  90.74% : {d_ho:+.2f} pts -> {'ABOVE' if d_ho > 0 else 'NOT above'}")
    print("Caveats: paper used 540 frames / WOSG filter / unknown split unit; protocols differ. "
          "Paper's hold-out is likely a random frame split, so it is not directly comparable to a grouped split.")
    res["paper"] = PAPER; res["n_windows"] = int(len(W)); res["n_groups"] = int(n_groups)
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(f"\nSaved {a.out}  ({time.time()-t0:.0f}s total)")

if __name__ == "__main__":
    main()
