#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hybrid_quantum_eeg_epilepsy.py
================================================================================
Hybrid quantum-classical EEG epilepsy detection - research implementation that
extends:

    Dash S., Dash D.K., Tripathy R.K., Pachori R.B. "Time-frequency domain
    machine learning for detection of epilepsy using wearable EEG sensor signals
    recorded during physical activities." Biomedical Signal Processing and
    Control 100 (2025) 107041.

Dataset: "Activities of Daily Livings using a Portable EEG Headset"
(NeuroSky MindWave 2.0, single dry FP1 electrode, 512 Hz, raw EEG).

Pipeline (all stages are executed by `python hybrid_quantum_eeg_epilepsy.py`):

    EEG -> dataset audit -> WOSG filtering -> 5 s windows -> GWST
        -> (a) 450-D [L1 | Shannon entropy] baseline  -> RF / SVM / MI+RF
        -> (b) log|GWST| temporal tokens [64, F] -> Linear(F,32)
               -> Transformer  OR  Bi-LSTM  (independent encoders)
               -> temporal attention pooling -> LayerNorm -> Linear(32,6) -> Tanh
               -> matched heads on the SAME 6-D embedding:
                  linear | MLP(6-6-1) | RBF-SVM | 6-qubit VQC | VQC w/o CNOT
        -> window probabilities -> recording-level mean probability
           -> validation-selected threshold -> recording-level decision

Additional studies: activity-wise / activity-group / leave-one-activity-out
evaluation, synthetic noise & artifact robustness, recording-level bootstrap
confidence intervals, paired comparisons, architecture diagrams, and
auto-generated reports.

INTEGRITY RULES BUILT INTO THIS SCRIPT
  * No number is hard-coded as a result. Published values of the base paper are
    only quoted (clearly labelled) in the comparison report.
  * Windows of one recording never cross train / validation / test boundaries.
  * Participant IDs are NOT available -> no participant-independent claim.
  * No claim of quantum advantage is made; the VQC is tested against matched
    classical heads on identical embeddings.
  * Threshold, normalisation (a0, per-frequency standardisation), feature
    selection, early stopping and every hyper-parameter choice use training /
    validation recordings only; the test partition is used for evaluation only.

USAGE
  python hybrid_quantum_eeg_epilepsy.py                       # full protocol
  python hybrid_quantum_eeg_epilepsy.py --profile quick       # 1 seed, shorter
  python hybrid_quantum_eeg_epilepsy_enhanced.py --profile enhanced # tuned research run
  python hybrid_quantum_eeg_epilepsy.py --profile smoke       # pipeline test
  python hybrid_quantum_eeg_epilepsy.py --data-path /path/to/zip_or_dir

Requirements: numpy scipy pandas scikit-learn matplotlib PyWavelets torch
              pennylane graphviz (python package + `dot` binary, optional;
              a Matplotlib fallback is used when Graphviz is unavailable)
================================================================================
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import io
import json
import logging
import math
import os
import platform
import random
import re
import shutil
import sys
import time
import traceback
import warnings
import zipfile
import zlib
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# =============================================================================
# USER-CONFIGURABLE PATHS (edit here, set env vars, or use CLI flags)
# =============================================================================
DATA_PATH = os.environ.get("EEG_DATA_PATH", "ADLs using a Portable EEG Headset.zip")
OUTPUT_ROOT = os.environ.get("EEG_OUTPUT_ROOT", "outputs")

# =============================================================================
# DEPENDENCIES (heavy imports guarded so that errors are explicit)
# =============================================================================
try:
    import scipy.fft as sfft
    from scipy import signal as sps
    from scipy import stats as spstats
except Exception as e:  # pragma: no cover
    raise RuntimeError("SciPy is required: %s" % e)

try:
    import pywt
except Exception as e:  # pragma: no cover
    raise RuntimeError("PyWavelets (pywt) is required for WOSG filtering: %s" % e)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except Exception as e:  # pragma: no cover
    raise RuntimeError("PyTorch is required: %s" % e)

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import (average_precision_score, roc_auc_score, log_loss)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import joblib

try:
    import pennylane as qml
    HAVE_PENNYLANE = True
    PENNYLANE_ERROR = ""
except Exception as e:  # pragma: no cover
    qml = None
    HAVE_PENNYLANE = False
    PENNYLANE_ERROR = repr(e)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

try:
    import graphviz as _graphviz
    HAVE_GRAPHVIZ_PY = True
except Exception:  # pragma: no cover
    _graphviz = None
    HAVE_GRAPHVIZ_PY = False
HAVE_DOT = shutil.which("dot") is not None


class DependencyError(RuntimeError):
    """Raised when a required dependency (e.g. PennyLane) is unavailable."""


# =============================================================================
# CONFIGURATION
# =============================================================================
class Cfg(dict):
    """dict with attribute access (read-only convenience for nested dicts)."""

    def __getattr__(self, k):
        try:
            v = self[k]
        except KeyError:
            raise AttributeError(k)
        return Cfg(v) if isinstance(v, dict) and not isinstance(v, Cfg) else v


def deep_update(base: dict, upd: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in upd.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_update(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


DEFAULT_CONFIG = {
    "profile": "full",
    "run": {
        "seeds": [0, 1, 2],
        "n_folds": 5,
        "max_folds": None,            # restrict #outer folds actually run (smoke tests)
        "run_baselines": True,
        "run_encoders": True,
        "run_quantum": True,          # if True and PennyLane missing -> DependencyError
        "run_finetune": True,         # separate end-to-end fine-tuning comparison
        "run_loao": True,
        "run_noise": True,
        "device": "auto",             # auto | cpu | cuda
        "num_threads": 2,
    },
    "data": {
        "path": DATA_PATH,
        "fs": 512,
        "nominal_duration_s": 20.0,
        "expected_samples": 10240,
        # 10,241 rows are found in the archive instead of the documented 10,240.
        #  keep_filter_drop_incomplete : filter all samples; non-overlapping 5 s windowing
        #                                uses complete windows only (the extra endpoint sample
        #                                falls into an incomplete trailing segment which is
        #                                reported and excluded - nothing is silently truncated)
        #  trim_to_nominal             : explicitly drop samples beyond 10,240 BEFORE filtering
        #  strict                      : raise if length != expected
        "length_policy": "keep_filter_drop_incomplete",
        "label_map": {"healthy": 0, "epilep": 1},
        "main_scope": "all",          # all (90 recordings) | paired (activities in both classes)
        "min_unique_values": 5,
    },
    "activity": {
        "canonical": ["desk work", "idle sitting", "laying", "sitting", "standing", "watching tv",
                      "cooking", "stairs", "walking", "jogging", "running", "jumping"],
        "aliases": {"deskwork": "desk work", "idlesitting": "idle sitting", "lying": "laying",
                    "watchingtv": "watching tv", "tv": "watching tv", "television": "watching tv",
                    "stairsupanddown": "stairs", "stair": "stairs", "stairsup": "stairs",
                    "jog": "jogging", "run": "running", "walk": "walking", "sit": "sitting",
                    "idle": "idle sitting", "desk": "desk work", "cook": "cooking", "jump": "jumping"},
        # Groups requested in the task specification
        "groups": {
            "stationary": ["desk work", "idle sitting", "sitting", "laying"],
            "light_ambulatory": ["walking", "stairs"],
            "intense_ambulatory": ["jogging", "running"],
        },
        # Healthy-only activities: group inferred from ReadMe code (00/01/02); they are
        # never used in binary activity-transfer experiments.
        "extra_group_from_readme": {"standing": "stationary", "watching tv": "stationary",
                                    "cooking": "light_ambulatory", "jumping": "intense_ambulatory"},
    },
    "wosg": {
        # Published WOSG (Gajbhiye et al., IEEE TIM 2021): DWT -> optimised Savitzky-Golay filter
        # applied to the artefact-contaminated APPROXIMATION sub-band -> subtract SG output from
        # the approximation -> add detail sub-bands back (inverse DWT).
        # NOT published (so configurable & documented as assumptions): wavelet, level, SG window
        # length, SG polynomial order and the optimisation criterion.
        "wavelet": "db4",
        "level": 7,                    # approximation band = 0 .. fs/2^(level+1) = 2 Hz at 512 Hz
        "mode": "symmetric",
        "optimize": True,              # grid-search (window, polyorder) per recording
        "window_candidates": [5, 9, 13, 17, 21, 31, 41, 51],
        "polyorder_candidates": [1, 2, 3],
        "fixed_window": 21,
        "fixed_polyorder": 2,
        "objective": "lowfreq_residual_plus_inband_decorrelation",
        "lambda_inband": 1.0,
        "lowfreq_cut_hz": 0.5,
        "inband_hz": [0.5, 50.0],
    },
    "window": {"seconds": 5.0, "overlap": 0.0},
    "gwst": {"n_freq": 225, "fmin": 0.5, "fmax": 50.0, "batch": 8},
    "features": {"entropy_bins": 10},
    "tokens": {"n_tokens": 64, "pool": 40, "token_dim": 32, "embed_dim": 6, "a0_stat": "median_of_window_freq_means"},
    "model": {
        "transformer": {"n_blocks": 2, "n_heads": 4, "ff_dim": 64, "dropout": 0.1},
        "bilstm": {"hidden": 16, "dropout": 0.1},
        "mlp_hidden": 6,
        "encoder_pretrain_head": "linear",
    },
    "quantum": {"n_qubits": 6, "n_layers": 2, "device": "default.qubit", "diff_method": "backprop",
                "init_std": 0.15, "entanglement": "ring"},
    "train": {
        "batch_size": 16, "optimizer": "AdamW", "weight_decay": 1e-4,
        "lr_encoder": 1e-3, "lr_head": 1e-2, "lr_quantum": 1e-2,
        "lr_finetune_encoder": 1e-4,
        "encoder_lr_grid": None,       # e.g. [1e-3, 3e-3]; None -> [lr_encoder]
        "head_lr_grid": None,          # e.g. [3e-3, 1e-2, 3e-2]; None -> [lr_head / lr_quantum]
        "max_epochs": 100, "patience": 15,
        "head_max_epochs": 100, "head_patience": 15,
        "ft_max_epochs": 100, "ft_patience": 15,
        "grad_clip": 1.0, "use_class_weights": True, "min_delta": 1e-5, "mixup_alpha": 0.15,
    },
    "classical": {
        "rf_grid": {"n_estimators": [10, 50, 200], "min_samples_leaf": [1, 3], "max_depth": [None, 6]},
        "svm_grid": {"kernel": ["linear", "rbf"], "C": [1.0, 10.0, 100.0]},
        "rbf_head_grid": {"C": [0.1, 1.0, 10.0, 100.0], "gamma": ["scale", 0.1, 1.0, 10.0]},
        "mi_k_grid": [10, 25, 50, 100, 225],
    },
    "cv": {"inner_val_splits": 4},
    "eval": {"n_bootstrap": 1000, "ci": 0.95, "bootstrap_seed": 2024},
    "loao": {"seeds": None, "models": "all"},   # seeds None -> all run seeds
    "noise": {
        "types": ["gaussian", "baseline_drift", "emg_like", "ocular_like"],
        "snr_db": [20, 10, 5], "seed": 12345, "seeds": None, "snr_reference": "raw",
        "emg_band_hz": [20.0, 200.0], "drift_freq_hz": [0.05, 0.5], "ocular_band_hz": [0.5, 4.0],
        "blink_rate_per_s": 0.3, "blink_width_s": 0.25,
    },
}

PROFILES = {
    "full": {},
    "quick": {
        "run": {"seeds": [0]},
        "train": {"max_epochs": 30, "patience": 6, "head_max_epochs": 40, "head_patience": 8,
                  "ft_max_epochs": 12, "ft_patience": 4},
        "eval": {"n_bootstrap": 300},
        "loao": {"seeds": [0], "models": ["E1", "E2", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11"]},
        "noise": {"seeds": [0]},
    },
    "enhanced": {
        # Research-grade retuning; same dataset/splits/metrics, more seeds and longer optimisation.
        "run": {"seeds": [0, 1, 2], "n_folds": 5, "max_folds": None},
        "train": {
            "max_epochs": 120, "patience": 20,
            "head_max_epochs": 160, "head_patience": 25,
            "ft_max_epochs": 120, "ft_patience": 20,
            "encoder_lr_grid": [0.0003, 0.001],
            "head_lr_grid": [0.001, 0.003, 0.01, 0.03],
            "lr_finetune_encoder": 0.00005,
            "weight_decay": 0.001,
            "mixup_alpha": 0.15,
        },
        "quantum": {"n_qubits": 6, "n_layers": 3, "device": "default.qubit", "diff_method": "backprop",
                    "init_std": 0.15, "entanglement": "ring"},
        "model": {"transformer": {"n_blocks": 2, "n_heads": 4, "ff_dim": 64, "dropout": 0.2},
                  "bilstm": {"hidden": 16, "dropout": 0.2}, "encoder_pretrain_head": "mlp"},
        "classical": {
            "rf_grid": {"n_estimators": [100, 300, 500], "min_samples_leaf": [1, 2, 3, 5], "max_depth": [None, 4, 6, 10]},
            "svm_grid": {"kernel": ["linear", "rbf"], "C": [0.1, 1.0, 10.0, 100.0]},
            "rbf_head_grid": {"C": [0.1, 1.0, 10.0, 100.0], "gamma": ["scale", 0.01, 0.1, 1.0, 10.0]},
            "mi_k_grid": [10, 25, 50, 100, 150, 225],
        },
        "eval": {"n_bootstrap": 1000},
        "loao": {"seeds": [0, 1, 2], "models": "all"},
        "noise": {"seeds": [0, 1, 2]},
    },
    "smoke": {
        "run": {"seeds": [0], "n_folds": 5, "max_folds": 2},
        "train": {"max_epochs": 3, "patience": 2, "head_max_epochs": 3, "head_patience": 2,
                  "ft_max_epochs": 2, "ft_patience": 2},
        "classical": {"rf_grid": {"n_estimators": [10], "min_samples_leaf": [1], "max_depth": [None]},
                      "svm_grid": {"kernel": ["rbf"], "C": [1.0]},
                      "rbf_head_grid": {"C": [1.0], "gamma": ["scale"]}, "mi_k_grid": [25]},
        "eval": {"n_bootstrap": 100},
        "wosg": {"window_candidates": [9, 21], "polyorder_candidates": [2]},
        "loao": {"seeds": [0], "models": ["E1", "E4", "E7", "E8"], "max_activities": 2},
        "noise": {"seeds": [0], "types": ["gaussian", "emg_like"], "snr_db": [10]},
    },
}


def build_config(profile: str, overrides: dict | None = None) -> Cfg:
    if profile not in PROFILES:
        raise ValueError("Unknown profile %s (choose from %s)" % (profile, list(PROFILES)))
    cfg = deep_update(DEFAULT_CONFIG, PROFILES[profile])
    cfg["profile"] = profile
    if overrides:
        cfg = deep_update(cfg, overrides)
    return Cfg(cfg)


# =============================================================================
# EXPERIMENT CATALOGUE
# =============================================================================
EXPERIMENTS = OrderedDict([
    ("E1", dict(name="GWST-450 + Random Forest", family="feature", mode="frozen/classical", enc=None)),
    ("E2", dict(name="GWST-450 + SVM", family="feature", mode="frozen/classical", enc=None)),
    ("E3", dict(name="GWST-450 + MI selection + Random Forest", family="feature", mode="frozen/classical", enc=None)),
    ("E4", dict(name="Transformer + 6-D embedding + linear", family="head", mode="frozen", enc="transformer", head="linear")),
    ("E5", dict(name="Transformer + 6-D embedding + MLP(6-6-1)", family="head", mode="frozen", enc="transformer", head="mlp")),
    ("E6", dict(name="Transformer + 6-D embedding + RBF-SVM", family="head", mode="frozen", enc="transformer", head="rbf_svm")),
    ("E7", dict(name="Transformer + 6-D embedding + 6-qubit VQC", family="head", mode="frozen", enc="transformer", head="vqc")),
    ("E8", dict(name="Bi-LSTM + 6-D embedding + linear", family="head", mode="frozen", enc="bilstm", head="linear")),
    ("E9", dict(name="Bi-LSTM + 6-D embedding + MLP(6-6-1)", family="head", mode="frozen", enc="bilstm", head="mlp")),
    ("E10", dict(name="Bi-LSTM + 6-D embedding + RBF-SVM", family="head", mode="frozen", enc="bilstm", head="rbf_svm")),
    ("E11", dict(name="Bi-LSTM + 6-D embedding + 6-qubit VQC", family="head", mode="frozen", enc="bilstm", head="vqc")),
    ("E12T", dict(name="Transformer + 6-D embedding + VQC without CNOT", family="head", mode="frozen", enc="transformer", head="vqc_nocnot")),
    ("E12B", dict(name="Bi-LSTM + 6-D embedding + VQC without CNOT", family="head", mode="frozen", enc="bilstm", head="vqc_nocnot")),
    ("FT-T-lin", dict(name="[fine-tuned] Transformer + linear", family="finetune", mode="end-to-end", enc="transformer", head="linear")),
    ("FT-T-mlp", dict(name="[fine-tuned] Transformer + MLP", family="finetune", mode="end-to-end", enc="transformer", head="mlp")),
    ("FT-T-vqc", dict(name="[fine-tuned] Transformer + VQC", family="finetune", mode="end-to-end", enc="transformer", head="vqc")),
    ("FT-B-lin", dict(name="[fine-tuned] Bi-LSTM + linear", family="finetune", mode="end-to-end", enc="bilstm", head="linear")),
    ("FT-B-mlp", dict(name="[fine-tuned] Bi-LSTM + MLP", family="finetune", mode="end-to-end", enc="bilstm", head="mlp")),
    ("FT-B-vqc", dict(name="[fine-tuned] Bi-LSTM + VQC", family="finetune", mode="end-to-end", enc="bilstm", head="vqc")),
])
QUANTUM_HEADS = ("vqc", "vqc_nocnot")


def exp_label(eid: str) -> str:
    return "%s %s" % (eid, EXPERIMENTS[eid]["name"])


# Okabe-Ito colour-blind safe palette
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]


# =============================================================================
# LOGGING / ENVIRONMENT / UTILITIES
# =============================================================================
LOG = logging.getLogger("eeg")
TLOG = logging.getLogger("eeg.train")


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    for lg in (LOG, TLOG):
        for h in list(lg.handlers):
            lg.removeHandler(h)
            with contextlib.suppress(Exception):
                h.close()
    LOG.setLevel(logging.DEBUG)
    LOG.propagate = False
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    fh = logging.FileHandler(log_dir / "experiment.log", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    eh = logging.FileHandler(log_dir / "error.log", encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(fmt)
    for h in (ch, fh, eh):
        LOG.addHandler(h)
    TLOG.setLevel(logging.DEBUG)
    TLOG.propagate = False
    th = logging.FileHandler(log_dir / "training.log", encoding="utf-8")
    th.setLevel(logging.INFO)
    th.setFormatter(fmt)
    tc = logging.StreamHandler(sys.stdout)
    tc.setLevel(logging.WARNING)
    tc.setFormatter(fmt)
    TLOG.addHandler(th)
    TLOG.addHandler(tc)


@contextlib.contextmanager
def stage(name: str):
    t0 = time.time()
    LOG.info("=" * 78)
    LOG.info("STAGE START : %s", name)
    try:
        yield
    except Exception:
        LOG.error("STAGE FAILED : %s\n%s", name, traceback.format_exc())
        raise
    LOG.info("STAGE DONE  : %s (%.1f s)", name, time.time() - t0)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2 ** 32 - 1))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (Path,)):
        return str(o)
    if isinstance(o, set):
        return sorted(o)
    return str(o)


def save_json(obj, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=json_default)


def pkg_versions() -> dict:
    out = {}
    for name in ["numpy", "scipy", "pandas", "sklearn", "matplotlib", "pywt", "torch", "pennylane",
                 "graphviz", "joblib"]:
        try:
            mod = sys.modules.get(name) or __import__(name)
            out[name] = getattr(mod, "__version__", "unknown")
        except Exception:
            out[name] = "not installed"
    return out


def environment_info(device: torch.device) -> dict:
    cuda = torch.cuda.is_available()
    return {
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "cpu_count": os.cpu_count(), "packages": pkg_versions(),
        "torch_version": torch.__version__, "pennylane_version": getattr(qml, "__version__", None) if qml else None,
        "pennylane_available": HAVE_PENNYLANE, "pennylane_error": PENNYLANE_ERROR,
        "cuda_available": cuda, "gpu_name": torch.cuda.get_device_name(0) if cuda else None,
        "device_used_for_classical_networks": str(device),
        "graphviz_python": HAVE_GRAPHVIZ_PY, "graphviz_dot_binary": HAVE_DOT,
        "torch_num_threads": torch.get_num_threads(),
        "note": "VQC simulation always runs on CPU (default.qubit statevector); classical networks use the device above.",
    }


def pick_device(pref: str) -> torch.device:
    if pref == "cpu":
        return torch.device("cpu")
    if pref == "cuda":
        if not torch.cuda.is_available():
            LOG.warning("CUDA requested but unavailable -> falling back to CPU")
            return torch.device("cpu")
        return torch.device("cuda")
    if torch.cuda.is_available():
        return torch.device("cuda")
    LOG.info("CUDA not available -> using CPU")
    return torch.device("cpu")


def df_to_md(df: pd.DataFrame, floatfmt: str = "%.4f", index: bool = False, max_rows: int | None = None) -> str:
    """Minimal markdown table writer (no tabulate dependency)."""
    if df is None or len(df) == 0:
        return "_(no rows)_\n"
    d = df.copy()
    if max_rows is not None:
        d = d.head(max_rows)
    if index:
        d = d.reset_index()
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in d.iterrows():
        cells = []
        for v in row.values:
            if isinstance(v, (float, np.floating)):
                cells.append("n/a" if not np.isfinite(v) else floatfmt % v)
            else:
                cells.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def fmt_ms(mean, std, n=None, nd=3) -> str:
    if mean is None or not np.isfinite(mean):
        return "n/a"
    s = ("%." + str(nd) + "f") % mean
    if std is not None and np.isfinite(std):
        s += " ± " + ("%." + str(nd) + "f") % std
    return s


# =============================================================================
# DATASET: reading, parsing, activity normalisation, audit
# =============================================================================
class DatasetSource:
    """Unified reader for a ZIP archive or an already-extracted directory."""

    def __init__(self, path):
        self.path = Path(path)
        self.kind = None
        self._zf = None
        self.entries: list[str] = []
        if self.path.is_file() and self.path.suffix.lower() == ".zip":
            self.kind = "zip"
            self._zf = zipfile.ZipFile(self.path)
            self.entries = [n for n in self._zf.namelist() if not n.endswith("/") and "__MACOSX" not in n
                            and not Path(n).name.startswith("._")]
        elif self.path.is_dir():
            self.kind = "directory"
            self.entries = sorted(str(p.relative_to(self.path)).replace("\\", "/")
                                  for p in self.path.rglob("*") if p.is_file())
            csvs = [e for e in self.entries if e.lower().endswith(".csv")]
            if not csvs:  # maybe a directory that contains the zip
                zips = [e for e in self.entries if e.lower().endswith(".zip")]
                if zips:
                    LOG.info("Directory contains ZIP %s -> reading the archive directly", zips[0])
                    self.path = self.path / zips[0]
                    self.kind = "zip"
                    self._zf = zipfile.ZipFile(self.path)
                    self.entries = [n for n in self._zf.namelist() if not n.endswith("/") and "__MACOSX" not in n]
        else:
            raise FileNotFoundError(
                "DATA_PATH '%s' is neither a .zip archive nor a directory. Set DATA_PATH at the top of the "
                "script, the EEG_DATA_PATH environment variable, or pass --data-path." % self.path)

    def read(self, rel: str) -> bytes:
        if self.kind == "zip":
            return self._zf.read(rel)
        return (self.path / rel).read_bytes()

    def close(self):
        if self._zf is not None:
            self._zf.close()


def parse_csv_bytes(raw: bytes) -> tuple[np.ndarray, dict]:
    """Robust single-column CSV parser. Never drops information silently: every anomaly is
    counted and returned in `issues`."""
    text = raw.decode("utf-8-sig", errors="replace")
    lines = re.split(r"\r\n|\r|\n", text)
    vals, issues = [], Counter()
    issues["n_lines_total"] = len(lines)
    header_seen = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == "":
            issues["n_blank_lines"] += 1
            continue
        toks = [t.strip() for t in re.split(r"[,;\t]", s)]
        if s.endswith((",", ";")):
            issues["n_trailing_delimiter_lines"] += 1
        nonempty = [t for t in toks if t != ""]
        if len(nonempty) > 1:
            issues["n_multi_column_lines"] += 1
        tok = nonempty[0] if nonempty else ""
        try:
            vals.append(float(tok))
        except ValueError:
            if i == 0 or (not vals and not header_seen):
                header_seen = True
                issues["header_present"] = 1
            else:
                issues["n_nonnumeric"] += 1
                vals.append(np.nan)
    return np.asarray(vals, dtype=np.float64), dict(issues)


def normalize_activity(stem: str, cfg: Cfg) -> tuple[str, str, bool]:
    """'01_walking 10' -> ('walking', '01', True). Filename suffix numbers are NOT participant IDs."""
    s = stem.lower().strip()
    m = re.match(r"^\s*(\d{1,2})\s*[_\-]\s*(.*)$", s)
    code = ""
    if m:
        code, s = m.group(1), m.group(2)
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\(?\s*\d+\s*\)?\s*$", "", s)           # trailing recording number
    s = re.sub(r"\s+", " ", s).strip()
    key = s.replace(" ", "")
    canon_keys = {c.replace(" ", ""): c for c in cfg.activity.canonical}
    if key in canon_keys:
        return canon_keys[key], code, True
    al = cfg.activity.aliases
    if key in al:
        return al[key], code, True
    return s, code, False


def activity_group(act: str, cfg: Cfg) -> str:
    for g, acts in cfg.activity.groups.items():
        if act in acts:
            return g
    return cfg.activity.extra_group_from_readme.get(act, "unassigned")


def label_from_path(rel: str, cfg: Cfg):
    low = rel.lower()
    for key, lab in cfg.data.label_map.items():
        if key in low:
            return lab
    return None


def analyze_signal(x: np.ndarray) -> dict:
    finite = np.isfinite(x)
    xf = x[finite]
    d = {"n_samples": int(len(x)), "n_nan": int((~finite).sum())}
    if len(xf) == 0:
        d.update(mean=np.nan, std=np.nan, min=np.nan, max=np.nan, n_unique=0, longest_flat_run=0)
        return d
    d.update(mean=float(xf.mean()), std=float(xf.std()), min=float(xf.min()), max=float(xf.max()),
             n_unique=int(len(np.unique(xf))))
    ch = np.flatnonzero(np.diff(xf) != 0)
    edges = np.concatenate([[-1], ch, [len(xf) - 1]])
    d["longest_flat_run"] = int(np.max(np.diff(edges))) if len(edges) > 1 else int(len(xf))
    d["first_equals_second"] = bool(len(xf) > 1 and xf[0] == xf[1])
    d["last_equals_previous"] = bool(len(xf) > 1 and xf[-1] == xf[-2])
    d["sha1"] = hashlib.sha1(np.ascontiguousarray(x).tobytes()).hexdigest()
    return d


def load_dataset(cfg: Cfg, data_path) -> tuple[dict, pd.DataFrame, dict]:
    """Load every CSV; return (signals {rec_id: raw array}, manifest DataFrame, audit dict).
    Recordings that cannot be modelled are EXCLUDED WITH A LOGGED REASON (never silently)."""
    src = DatasetSource(data_path)
    LOG.info("Dataset source: %s (%s)", src.path, src.kind)
    fs = cfg.data.fs
    expected = int(cfg.data.expected_samples)
    readme_text, desc_text = "", ""
    for e in src.entries:
        nm = Path(e).name.lower()
        try:
            if nm == "readme.txt":
                readme_text = src.read(e).decode("utf-8", errors="replace")
            elif nm.endswith(".docx") and "description" in nm:
                x = zipfile.ZipFile(io.BytesIO(src.read(e))).read("word/document.xml").decode("utf-8", "replace")
                desc_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip()
        except Exception as ex:  # pragma: no cover
            LOG.warning("Could not read documentation file %s: %s", e, ex)

    rows, signals, used_ids = [], {}, Counter()
    for rel in sorted(e for e in src.entries if e.lower().endswith(".csv")):
        label = label_from_path(rel, cfg)
        stem = Path(rel).stem
        act, code, known = normalize_activity(stem, cfg)
        raw = src.read(rel)
        x, issues = parse_csv_bytes(raw)
        info = analyze_signal(x)
        cname = "Healthy Individuals" if label == 0 else ("Epileptic Patients" if label == 1 else "UNKNOWN")
        base_id = ("H_" if label == 0 else "E_" if label == 1 else "U_") + re.sub(r"\W+", "_", stem).strip("_")
        used_ids[base_id] += 1
        rec_id = base_id if used_ids[base_id] == 1 else "%s__dup%d" % (base_id, used_ids[base_id])
        reasons = []
        if label is None:
            reasons.append("class folder not recognised")
        if len(x) == 0:
            reasons.append("empty file")
        if info["n_nan"] > 0:
            reasons.append("%d missing/non-numeric samples" % info["n_nan"])
        if len(x) > 0 and info.get("std", 0) == 0:
            reasons.append("constant signal")
        elif len(x) > 0 and info["n_unique"] < cfg.data.min_unique_values:
            reasons.append("too few unique values (%d)" % info["n_unique"])
        if issues.get("n_multi_column_lines", 0) > 0:
            reasons.append("multi-column lines present")
        win_n = int(round(cfg.window.seconds * fs))
        if len(x) < win_n:
            reasons.append("shorter than one %.1f s window" % cfg.window.seconds)
        if cfg.data.length_policy == "strict" and len(x) != expected:
            raise ValueError("length_policy='strict': %s has %d samples (expected %d)" % (rel, len(x), expected))
        row = dict(rec_id=rec_id, rel_path=rel, class_name=cname, label=label if label is not None else -1,
                   activity_raw=stem, activity=act, activity_known=known, filename_code=code,
                   activity_group=activity_group(act, cfg), n_samples=len(x),
                   duration_s=len(x) / fs, excess_vs_nominal=len(x) - expected,
                   parse_trailing_delim=issues.get("n_trailing_delimiter_lines", 0),
                   parse_blank_lines=issues.get("n_blank_lines", 0),
                   parse_nonnumeric=issues.get("n_nonnumeric", 0), parse_header=issues.get("header_present", 0),
                   **{k: v for k, v in info.items() if k not in ("n_samples",)})
        row["excluded"] = len(reasons) > 0
        row["exclusion_reason"] = "; ".join(reasons)
        rows.append(row)
        if not reasons:
            signals[rec_id] = x
        else:
            LOG.warning("EXCLUDED recording %s: %s", rel, row["exclusion_reason"])
    src.close()
    man = pd.DataFrame(rows)
    if len(man) == 0:
        raise RuntimeError("No CSV recordings found under %s" % data_path)

    # --- global / cross-recording audit -------------------------------------
    gmin, gmax = float(man["min"].min()), float(man["max"].max())
    sat = {}
    for rid, x in signals.items():
        sat[rid] = float(np.mean((x <= gmin + 1e-9) | (x >= gmax - 1e-9)))
    man["saturation_fraction_global_extremes"] = man["rec_id"].map(sat)
    man["duplicate_of"] = ""
    dup = man.groupby("sha1")["rec_id"].apply(list)
    for lst in dup:
        if len(lst) > 1:
            for r in lst[1:]:
                man.loc[man.rec_id == r, "duplicate_of"] = lst[0]
    std_ok = man.loc[~man.excluded, "std"]
    med, mad = float(std_ok.median()), float((std_ok - std_ok.median()).abs().median()) + 1e-12
    man["std_robust_z"] = (man["std"] - med) / (1.4826 * mad)
    man["unusual_std_flag"] = man["std_robust_z"].abs() > 6.0

    len_counts = Counter(int(n) for n in man["n_samples"])
    mode_len = len_counts.most_common(1)[0][0]
    n_last_dup = int(man["last_equals_previous"].fillna(False).sum())
    n_first_dup = int(man["first_equals_second"].fillna(False).sum())
    cls_act = man[~man.excluded].groupby(["activity", "label"]).size().unstack(fill_value=0)
    eligible = sorted(a for a in cls_act.index if (cls_act.loc[a] > 0).all() and cls_act.shape[1] == 2)
    only_one = sorted(a for a in cls_act.index if a not in eligible)

    audit = {
        "data_source": str(src.path), "source_kind": src.kind,
        "documented": {"sampling_rate_hz": fs, "duration_s": cfg.data.nominal_duration_s,
                       "expected_samples": expected, "files": 90, "healthy": 60, "epilepsy": 30},
        "found": {"csv_files": int(len(man)), "healthy": int((man.label == 0).sum()),
                  "epilepsy": int((man.label == 1).sum()), "excluded": int(man.excluded.sum()),
                  "unknown_activity_names": sorted(set(man.loc[~man.activity_known, "activity"]))},
        "length_analysis": {
            "length_counts": {str(k): v for k, v in sorted(len_counts.items())},
            "modal_length": mode_len, "excess_vs_expected": mode_len - expected,
            "all_recordings_same_length": len(len_counts) == 1,
            "n_files_header_present": int(man.parse_header.sum()),
            "n_files_with_blank_lines_beyond_final_newline": int((man.parse_blank_lines > 1).sum()),
            "n_files_last_equals_previous_sample": n_last_dup,
            "n_files_first_equals_second_sample": n_first_dup,
            "n_files_trailing_delimiter": int((man.parse_trailing_delim > 0).sum()),
            "files_trailing_delimiter": man.loc[man.parse_trailing_delim > 0, "rel_path"].tolist(),
            "interpretation": (
                "Every recording has %d numeric rows (documented: %d = 20 s x %d Hz). The excess is exactly %d "
                "sample(s) in every file, with no header row, no extra column and no malformed row. "
                "This systematic pattern is consistent with INCLUSIVE ENDPOINT SAMPLING (t = 0 ... 20 s gives "
                "20*512+1 samples) or a single extra sample logged at acquisition start/stop. It is NOT a "
                "formatting artefact (a trailing newline is counted separately and only %d file(s) carry a "
                "trailing-comma formatting quirk). The raw files alone cannot prove which acquisition mechanism "
                "produced the sample; this is an inference, not a verified fact." % (
                    mode_len, expected, fs, mode_len - expected, int((man.parse_trailing_delim > 0).sum()))),
            "policy": cfg.data.length_policy,
            "policy_explanation": {
                "keep_filter_drop_incomplete": "All samples are filtered; non-overlapping 5 s windowing yields "
                                               "floor(N/2560) complete windows; the trailing incomplete segment "
                                               "(N mod 2560 samples) is reported per recording and excluded.",
                "trim_to_nominal": "Samples beyond 10,240 are removed before filtering (explicit & logged).",
                "strict": "Abort if any recording differs from 10,240 samples."}[cfg.data.length_policy],
        },
        "amplitude": {"global_min": gmin, "global_max": gmax,
                      "median_recording_std": med,
                      "note": "Values are quantised (see manifest n_unique) and many recordings touch the global "
                              "min/max; saturation/clipping of the dry-electrode headset is likely (fraction per "
                              "recording in manifest column saturation_fraction_global_extremes)."},
        "duplicates": {"n_duplicate_recordings": int((man.duplicate_of != "").sum()),
                       "pairs": man.loc[man.duplicate_of != "", ["rec_id", "duplicate_of"]].values.tolist()},
        "unusual_std_recordings": man.loc[man.unusual_std_flag, "rec_id"].tolist(),
        "constant_recordings": man.loc[man["std"] == 0, "rec_id"].tolist(),
        "exclusions": man.loc[man.excluded, ["rec_id", "exclusion_reason"]].values.tolist(),
        "class_activity_counts": {str(a): {("healthy" if c == 0 else "epilepsy"): int(v) for c, v in row.items()}
                                  for a, row in cls_act.iterrows()},
        "eligible_activities_both_classes": eligible,
        "single_class_activities_excluded_from_transfer": only_one,
        "readme_text": readme_text, "description_docx_text": desc_text,
        "participant_ids_available": False,
        "participant_id_warning": ("The archive provides NO participant identifiers. Numbers in file names are "
                                   "recording counters per activity and are NOT interpreted as subject IDs. "
                                   "Recording-level grouping prevents window leakage but multiple recordings may "
                                   "come from the same person, so participant-independent generalisation cannot be "
                                   "claimed."),
        "readme_code_check": {},
    }
    # compare filename code (00/01/02) with name-based group mapping
    mism = []
    code_map = {"00": "stationary", "01": "light_ambulatory", "02": "intense_ambulatory"}
    for _, r in man.iterrows():
        if r.filename_code in code_map and r.activity_group != code_map[r.filename_code]:
            mism.append((r.rec_id, r.filename_code, r.activity_group))
    audit["readme_code_check"] = {"mismatches": mism, "n_mismatches": len(mism)}
    LOG.info("Audit: %d CSV (%d healthy / %d epilepsy), %d excluded, modal length %d (expected %d)",
             len(man), (man.label == 0).sum(), (man.label == 1).sum(), man.excluded.sum(), mode_len, expected)
    return signals, man, audit


def apply_length_policy(x: np.ndarray, cfg: Cfg) -> np.ndarray:
    if cfg.data.length_policy == "trim_to_nominal":
        return x[: int(cfg.data.expected_samples)]
    return x


# =============================================================================
# WOSG: wavelet-domain optimised Savitzky-Golay filtering
# =============================================================================
def _fft_band(x: np.ndarray, fs: float, lo: float, hi: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    X[(f < lo) | (f >= hi)] = 0
    return np.fft.irfft(X, n=len(x))


def _lowpower(x: np.ndarray, fs: float, cut: float) -> float:
    X = np.fft.rfft(x - x.mean())
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    return float(np.sum(np.abs(X[(f > 0) & (f < cut)]) ** 2) / len(x) ** 2)


def wosg_filter(x: np.ndarray, fs: float, wcfg: dict) -> tuple[np.ndarray, dict]:
    """Wavelet-domain optimised Savitzky-Golay (WOSG) motion-artefact removal.

    Published structure (Gajbhiye et al. 2021): x -> DWT; the low-frequency motion artefact lives in
    the approximation sub-band cA; an SG filter estimates the artefact in cA; cleaned cA = cA - SG(cA);
    inverse DWT of [cleaned cA, details] gives the filtered EEG.

    Implementation assumptions (not published, therefore configurable):
      * wavelet / decomposition level from `wcfg`.
      * (window length, polynomial order) chosen per recording by grid search minimising
            J = P_low(clean)/P_low(raw) + lambda * (1 - corr_inband(clean, raw))
        where P_low is power below `lowfreq_cut_hz` (drift removal) and corr_inband is the Pearson
        correlation within `inband_hz` (preservation of EEG content). This is an unsupervised proxy because
        no clean reference EEG exists; it is NOT the optimisation criterion of the original paper.
    """
    x = np.asarray(x, dtype=np.float64)
    wavelet, mode = wcfg["wavelet"], wcfg["mode"]
    level = min(int(wcfg["level"]), pywt.dwt_max_level(len(x), pywt.Wavelet(wavelet).dec_len))
    coeffs = pywt.wavedec(x, wavelet, level=level, mode=mode)
    cA, details = coeffs[0], coeffs[1:]
    n_a = len(cA)

    def reconstruct(w, p):
        w = int(w)
        if w % 2 == 0:
            w += 1
        w = min(w, n_a if n_a % 2 == 1 else n_a - 1)
        p = min(int(p), w - 1)
        art = sps.savgol_filter(cA, w, p, mode="interp")
        y = pywt.waverec([cA - art] + list(details), wavelet, mode=mode)[: len(x)]
        return y, w, p

    info = {"wavelet": wavelet, "level": level, "mode": mode, "approx_len": n_a,
            "approx_sampling_hz": fs / (2 ** level), "approx_band_hz": [0.0, fs / (2 ** (level + 1))],
            "optimized": bool(wcfg["optimize"])}
    if not wcfg["optimize"]:
        y, w, p = reconstruct(wcfg["fixed_window"], wcfg["fixed_polyorder"])
        info.update(window=w, polyorder=p, cost=None)
        return y, info

    lo_cut = float(wcfg["lowfreq_cut_hz"])
    band = wcfg["inband_hz"]
    raw_low = _lowpower(x, fs, lo_cut) + 1e-18
    raw_band = _fft_band(x, fs, band[0], band[1])
    best = (np.inf, None, None, None)
    grid = []
    for w in wcfg["window_candidates"]:
        for p in wcfg["polyorder_candidates"]:
            if w <= p:
                continue
            if int(w) > n_a:
                continue
            y, w2, p2 = reconstruct(w, p)
            cl = _fft_band(y, fs, band[0], band[1])
            denom = (raw_band.std() * cl.std()) + 1e-18
            corr = float(np.mean((raw_band - raw_band.mean()) * (cl - cl.mean())) / denom)
            J = _lowpower(y, fs, lo_cut) / raw_low + float(wcfg["lambda_inband"]) * (1.0 - corr)
            grid.append((w2, p2, J))
            if J < best[0]:
                best = (J, y, w2, p2)
    if best[1] is None:  # no valid candidate (very short approx) -> fixed fallback
        y, w, p = reconstruct(wcfg["fixed_window"], wcfg["fixed_polyorder"])
        info.update(window=w, polyorder=p, cost=None, fallback=True)
        return y, info
    info.update(window=int(best[2]), polyorder=int(best[3]), cost=float(best[0]))
    return best[1], info


def filter_all_recordings(signals: dict, cfg: Cfg) -> tuple[dict, dict, dict]:
    """Return (raw_used, filtered, wosg_info) for every modelled recording."""
    raw_used, filt, infos = {}, {}, {}
    for rid, x in signals.items():
        xr = apply_length_policy(x, cfg)
        y, info = wosg_filter(xr, cfg.data.fs, cfg.wosg)
        raw_used[rid], filt[rid], infos[rid] = xr, y, info
    return raw_used, filt, infos


# =============================================================================
# SEGMENTATION
# =============================================================================
def segment_signal(x: np.ndarray, win: int, hop: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Complete windows only. Returns (windows [n, win], start indices, leftover samples)."""
    if len(x) < win:
        return np.zeros((0, win)), np.zeros(0, dtype=int), len(x)
    n = (len(x) - win) // hop + 1
    starts = np.arange(n) * hop
    W = np.stack([x[s:s + win] for s in starts])
    leftover = len(x) - (starts[-1] + win)
    return W, starts, int(leftover)


# =============================================================================
# GAUSSIAN-WINDOW STOCKWELL TRANSFORM (GWST)
# =============================================================================
class GWST:
    """Gaussian-window Stockwell transform following Eq. (1)-(3) of the base paper:

        Z(k)        = (1/N) sum_n z(n) exp(-j 2 pi n k / N)                     (3)
        W(m,k)      = exp(-2 pi^2 m^2 / k^2)                                    (2)
        T(n,k)      = sum_m Z(m+k) W(m,k) exp(+j 2 pi m n / N)                  (1)

    * Frequency voices are `freqs` (Hz) <-> k = f N / fs. Because 0.5-50 Hz sampled on 225 points is not on
      the integer DFT grid for N = 2560 (df = 0.2 Hz), k is generally FRACTIONAL. Z(m + k) for fractional k is
      evaluated EXACTLY (not interpolated) via the DTFT of z(n) exp(-j 2 pi n eps / N), eps = frac(k).
    * The Gaussian window is symmetric and periodic in m (m = -N/2 ... N/2-1), i.e. the standard S-transform
      window; Eq. (1) summed literally over m = 0..N-1 would only use one half of the Gaussian.
    * Complex128 arithmetic; no log/exp of tiny numbers beyond exp(-x) underflow to 0 (safe).
    """

    def __init__(self, n_samples: int, fs: float, freqs: np.ndarray):
        self.N = int(n_samples)
        self.fs = float(fs)
        self.freqs = np.asarray(freqs, dtype=np.float64)
        k = self.freqs * self.N / self.fs
        if np.any(k <= 0):
            raise ValueError("GWST frequencies must be > 0 Hz")
        self.k = k
        self.K = np.floor(k).astype(np.int64)
        eps = k - self.K
        n = np.arange(self.N)
        self.E = np.exp(-2j * np.pi * np.outer(eps, n) / self.N)
        m = np.fft.fftfreq(self.N, d=1.0 / self.N).astype(np.int64)
        self.W = np.exp(-2.0 * np.pi ** 2 * (m[None, :].astype(np.float64) ** 2) / (k[:, None] ** 2))
        self.idx = (m[None, :] + self.K[:, None]) % self.N

    def transform(self, z: np.ndarray) -> np.ndarray:
        """z [N] -> complex T [n_freq, N]."""
        z = np.asarray(z, dtype=np.float64)
        Ze = sfft.fft(z[None, :] * self.E, axis=1, workers=2) / self.N
        A = np.take_along_axis(Ze, self.idx, axis=1) * self.W
        return sfft.ifft(A, axis=1, workers=2) * self.N

    def magnitude(self, windows: np.ndarray) -> np.ndarray:
        """windows [B, N] -> |T| float32 [B, n_freq, N]."""
        out = np.empty((len(windows), len(self.freqs), self.N), dtype=np.float32)
        for i, w in enumerate(windows):
            out[i] = np.abs(self.transform(w)).astype(np.float32)
        return out


def naive_stockwell_integer_k(z: np.ndarray, ks: list[int]) -> np.ndarray:
    """Direct O(N^2) evaluation of Eq. (1)-(3) for INTEGER k (used only in self-tests)."""
    N = len(z)
    n = np.arange(N)
    Z = np.array([np.sum(z * np.exp(-2j * np.pi * n * kk / N)) / N for kk in range(N)])
    out = np.zeros((len(ks), N), dtype=complex)
    for r, k in enumerate(ks):
        for nn_ in range(N):
            acc = 0j
            for m in range(-N // 2, N // 2):
                acc += Z[(m + k) % N] * np.exp(-2 * np.pi ** 2 * m ** 2 / k ** 2) * np.exp(2j * np.pi * m * nn_ / N)
            out[r, nn_] = acc
    return out


# =============================================================================
# FEATURES: L1 norm + Shannon entropy (450-D) and temporal tokens
# =============================================================================
def row_entropy(A: np.ndarray, bins: int) -> np.ndarray:
    """Shannon entropy (bits) of the normalised histogram (`bins` equal-width bins) of every row of
    A [R, N]. Empty bins / zero probabilities are handled safely (0 log 0 := 0); a constant row has 0 entropy."""
    R, N = A.shape
    mn = A.min(axis=1, keepdims=True)
    rg = A.max(axis=1, keepdims=True) - mn
    safe = np.where(rg > 0, rg, 1.0)
    idx = np.minimum(((A - mn) / safe * bins).astype(np.int64), bins - 1)
    idx = np.where(rg > 0, idx, 0)
    counts = np.bincount((idx + (np.arange(R)[:, None] * bins)).ravel(), minlength=R * bins).reshape(R, bins)
    p = counts / float(N)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.where(p > 0, p * np.log2(np.where(p > 0, p, 1.0)), 0.0).sum(axis=1)
    return h


def l1_entropy_features(Smag: np.ndarray, bins: int) -> np.ndarray:
    """Smag [B, F, N] -> [B, 2F] = [L1 norms | Shannon entropies] (paper Eq. 4-5)."""
    B, Fq, N = Smag.shape
    l1 = Smag.sum(axis=2, dtype=np.float64)
    ent = row_entropy(Smag.reshape(B * Fq, N).astype(np.float64), bins).reshape(B, Fq)
    return np.concatenate([l1, ent], axis=1).astype(np.float32)


class TokenScaler:
    """log(1 + |GWST|/a0) -> mean-pool `pool` consecutive samples -> [n, n_tokens, F] -> per-frequency
    standardisation. a0 and the standardisation statistics are fitted on TRAINING windows only."""

    def __init__(self, n_tokens: int, pool: int):
        self.T, self.pool = int(n_tokens), int(pool)
        self.a0 = None
        self.mu = None
        self.sd = None

    def fit_a0(self, mean_mag_train: np.ndarray) -> None:
        a0 = float(np.median(mean_mag_train))
        self.a0 = a0 if a0 > 0 else float(np.mean(mean_mag_train) + 1e-12)

    def raw_tokens(self, S, chunk: int = 32) -> np.ndarray:
        outs = []
        for i in range(0, len(S), chunk):
            s = np.asarray(S[i:i + chunk], dtype=np.float32)
            n, Fq, N = s.shape
            use = self.T * self.pool
            if N < use:
                raise ValueError("GWST time axis (%d) shorter than n_tokens*pool (%d)" % (N, use))
            L = np.log1p(s[:, :, :use] / np.float32(self.a0))
            L = L.reshape(n, Fq, self.T, self.pool).mean(axis=3)
            outs.append(L.transpose(0, 2, 1))
        return np.concatenate(outs, axis=0) if outs else np.zeros((0, self.T, 0), np.float32)

    def fit_standardizer(self, tok_train: np.ndarray) -> None:
        self.mu = tok_train.mean(axis=(0, 1)).astype(np.float32)
        self.sd = (tok_train.std(axis=(0, 1)) + 1e-6).astype(np.float32)

    def standardize(self, tok: np.ndarray) -> np.ndarray:
        return ((tok - self.mu) / self.sd).astype(np.float32)

    def transform(self, S) -> np.ndarray:
        return self.standardize(self.raw_tokens(S))


# =============================================================================
# DATA SPLITTING (recording-level grouping, no window leakage)
# =============================================================================
def partition_summary(win_df: pd.DataFrame, rec_idx_set) -> dict:
    sub = win_df[win_df.rec_idx.isin(rec_idx_set)]
    r = sub.drop_duplicates("rec_idx")
    return {"n_recordings": int(len(r)), "n_windows": int(len(sub)),
            "healthy_recordings": int((r.label == 0).sum()), "epilepsy_recordings": int((r.label == 1).sum()),
            "activity_counts": r.activity.value_counts().to_dict()}


def outer_folds(win_df: pd.DataFrame, pool_mask: np.ndarray, n_folds: int, seed: int):
    """StratifiedGroupKFold over windows with RECORDING as the group. Returns list of (train_win_idx, test_win_idx)
    (global window indices). Raises if a valid grouped stratified split is impossible."""
    idx = np.flatnonzero(pool_mask)
    y = win_df.label.values[idx]
    g = win_df.rec_idx.values[idx]
    rec_per_class = pd.Series(g).groupby(y).nunique()
    if rec_per_class.min() < n_folds:
        raise ValueError("Cannot form %d grouped stratified folds: recordings per class = %s. Stopping instead of "
                         "falling back to a window-level random split." % (n_folds, rec_per_class.to_dict()))
    sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    folds = []
    for tr, te in sgkf.split(np.zeros(len(idx)), y, groups=g):
        tr_g, te_g = idx[tr], idx[te]
        assert not (set(win_df.rec_idx.values[tr_g]) & set(win_df.rec_idx.values[te_g])), "recording leakage!"
        if len(set(win_df.label.values[te_g])) < 2:
            raise ValueError("A test fold contains a single class; cannot continue with grouped stratification.")
        folds.append((tr_g, te_g))
    return folds


def inner_split(win_df: pd.DataFrame, train_idx: np.ndarray, n_splits: int, seed: int):
    """Recording-level validation partition inside a training set -> (train_idx, val_idx)."""
    y = win_df.label.values[train_idx]
    g = win_df.rec_idx.values[train_idx]
    last_err = None
    for attempt in range(10):
        sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + 7919 * attempt)
        try:
            tr, va = next(iter(sgkf.split(np.zeros(len(train_idx)), y, groups=g)))
        except ValueError as e:
            last_err = e
            continue
        if len(set(y[va])) == 2 and len(set(y[tr])) == 2:
            a, b = train_idx[tr], train_idx[va]
            assert not (set(win_df.rec_idx.values[a]) & set(win_df.rec_idx.values[b]))
            return a, b
    raise ValueError("Could not form a two-class recording-level validation partition (%s)" % last_err)


# =============================================================================
# METRICS
# =============================================================================
METRIC_COLS = ["accuracy", "balanced_accuracy", "precision", "sensitivity", "specificity", "f1",
               "macro_f1", "roc_auc", "pr_auc", "mcc"]


def compute_metrics(y_true, y_prob, y_pred) -> dict:
    """All metrics where mathematically valid; NaN (= unavailable) otherwise - never invented."""
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    n = len(y_true)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    P, Nn = tp + fn, tn + fp
    nan = float("nan")
    d = {"n": n, "n_pos": P, "n_neg": Nn, "tp": tp, "tn": tn, "fp": fp, "fn": fn}
    d["accuracy"] = (tp + tn) / n if n else nan
    d["sensitivity"] = tp / P if P else nan
    d["specificity"] = tn / Nn if Nn else nan
    d["balanced_accuracy"] = 0.5 * (d["sensitivity"] + d["specificity"]) if (P and Nn) else nan
    d["precision"] = tp / (tp + fp) if (tp + fp) else nan
    d["f1"] = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else nan
    f1_0 = 2 * tn / (2 * tn + fn + fp) if (2 * tn + fn + fp) else nan
    d["macro_f1"] = float(np.nanmean([d["f1"], f1_0])) if (np.isfinite(d["f1"]) and np.isfinite(f1_0)) else nan
    den = math.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    d["mcc"] = (tp * tn - fp * fn) / den if (den > 0 and P and Nn) else nan
    if P and Nn and y_prob is not None:
        d["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        d["pr_auc"] = float(average_precision_score(y_true, y_prob))
    else:
        d["roc_auc"] = d["pr_auc"] = nan
    return d


def select_threshold(y, p) -> float:
    """Threshold maximising balanced accuracy on VALIDATION data only (ties -> closest to 0.5).
    Falls back to 0.5 if validation has a single class."""
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    if len(set(y)) < 2:
        return 0.5
    u = np.unique(p)
    cands = np.unique(np.concatenate([[0.5], u, (u[:-1] + u[1:]) / 2.0 if len(u) > 1 else []]))
    best, best_t = -1.0, 0.5
    for t in cands:
        pred = (p >= t).astype(int)
        sens = np.mean(pred[y == 1] == 1)
        spec = np.mean(pred[y == 0] == 0)
        ba = 0.5 * (sens + spec)
        if ba > best + 1e-12 or (abs(ba - best) <= 1e-12 and abs(t - 0.5) < abs(best_t - 0.5)):
            best, best_t = ba, float(t)
    return best_t


def fast_batch_metrics(y: np.ndarray, pred: np.ndarray, prob: np.ndarray) -> dict:
    """Vectorised metrics over B bootstrap replicates. y,pred,prob: [B, R]. Returns dict of [B] arrays (NaN if invalid)."""
    yb = y.astype(bool)
    pb = pred.astype(bool)
    tp = (yb & pb).sum(1).astype(float)
    tn = (~yb & ~pb).sum(1).astype(float)
    fp = (~yb & pb).sum(1).astype(float)
    fn = (yb & ~pb).sum(1).astype(float)
    P, Nn = tp + fn, tn + fp
    ok = (P > 0) & (Nn > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        sens = tp / P
        spec = tn / Nn
        acc = (tp + tn) / (P + Nn)
        ba = np.where(ok, 0.5 * (sens + spec), np.nan)
        f1 = 2 * tp / (2 * tp + fp + fn)
        f1n = 2 * tn / (2 * tn + fn + fp)
        mf1 = np.where(ok, 0.5 * (f1 + f1n), np.nan)
        den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        mcc = np.where(ok & (den > 0), (tp * tn - fp * fn) / den, np.nan)
        ranks = spstats.rankdata(prob, axis=1)
        auc = np.where(ok, (np.where(yb, ranks, 0).sum(1) - P * (P + 1) / 2) / (P * Nn), np.nan)
    return {"accuracy": acc, "balanced_accuracy": ba, "sensitivity": np.where(ok, sens, np.nan),
            "specificity": np.where(ok, spec, np.nan), "macro_f1": mf1, "mcc": mcc, "roc_auc": auc}


# =============================================================================
# NEURAL MODELS
# =============================================================================
class AttnPool(nn.Module):
    """Temporal attention pooling: softmax_t(w^T tanh(W h_t)) weighted sum."""

    def __init__(self, d: int):
        super().__init__()
        self.score = nn.Sequential(nn.Linear(d, d), nn.Tanh(), nn.Linear(d, 1, bias=False))

    def forward(self, x):                       # x [B,T,d]
        a = torch.softmax(self.score(x).squeeze(-1), dim=1)
        return (a.unsqueeze(-1) * x).sum(dim=1)


class SinusoidalPE(nn.Module):
    def __init__(self, d: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d)
        pos = torch.arange(max_len).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d, 2).float() * (-math.log(10000.0) / d))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div[: d // 2])
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x):
        return x + self.pe[:, : x.size(1)]


class PreNormBlock(nn.Module):
    def __init__(self, d, heads, ff, drop):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(d, heads, dropout=drop, batch_first=True)
        self.ff = nn.Sequential(nn.Linear(d, ff), nn.GELU(), nn.Dropout(drop), nn.Linear(ff, d))
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        h = self.ln1(x)
        x = x + self.drop(self.attn(h, h, h, need_weights=False)[0])     # residual
        x = x + self.drop(self.ff(self.ln2(x)))                           # residual
        return x


class TransformerCore(nn.Module):
    def __init__(self, d, c):
        super().__init__()
        self.pe = SinusoidalPE(d)
        self.blocks = nn.ModuleList([PreNormBlock(d, c["n_heads"], c["ff_dim"], c["dropout"])
                                     for _ in range(c["n_blocks"])])
        self.ln = nn.LayerNorm(d)
        self.pool = AttnPool(d)

    def forward(self, x):
        x = self.pe(x)
        for b in self.blocks:
            x = b(x)
        return self.pool(self.ln(x))


class BiLSTMCore(nn.Module):
    def __init__(self, d, c):
        super().__init__()
        self.lstm = nn.LSTM(d, c["hidden"], num_layers=1, batch_first=True, bidirectional=True)
        self.drop = nn.Dropout(c["dropout"])
        self.pool = AttnPool(2 * c["hidden"])

    def forward(self, x):
        h, _ = self.lstm(x)
        return self.pool(self.drop(h))


class EEGEncoder(nn.Module):
    """[B,64,F] -> Linear(F,32) -> Transformer | Bi-LSTM -> attention pooling [B,32]
       -> LayerNorm(32) -> Linear(32,6) -> Tanh -> [B,6]  (the shared 6-D embedding)."""

    def __init__(self, kind: str, n_freq: int, cfg: Cfg):
        super().__init__()
        d = cfg.tokens.token_dim
        self.kind = kind
        self.proj = nn.Linear(n_freq, d)
        if kind == "transformer":
            self.core = TransformerCore(d, cfg.model.transformer)
        elif kind == "bilstm":
            self.core = BiLSTMCore(d, cfg.model.bilstm)
        else:
            raise ValueError(kind)
        self.embed = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, cfg.tokens.embed_dim), nn.Tanh())

    def encode32(self, x):
        return self.core(self.proj(x))

    def forward(self, x):
        return self.embed(self.encode32(x))


class LinearHead(nn.Module):
    def __init__(self, d=6):
        super().__init__()
        self.fc = nn.Linear(d, 1)

    def forward(self, z):
        return self.fc(z).squeeze(-1)


class MLPHead(nn.Module):
    """6 -> 6 -> 1 with Tanh."""

    def __init__(self, d=6, h=6):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, h), nn.Tanh(), nn.Linear(h, 1))

    def forward(self, z):
        return self.net(z).squeeze(-1)


class QuantumHead(nn.Module):
    """Six-qubit variational quantum classifier (PennyLane, PyTorch interface, differentiable
    statevector simulator `default.qubit`).

      |0>^6 -> RY(pi * z_i) -> [ RY(theta) RZ(phi) on every qubit -> CNOT ring 0->1->...->5->0 ] x n_layers
            -> <Z_i> (i=0..5) -> Linear(6,1) -> logit

    `entangle=False` removes the CNOT ring (experiment E12). No classical layer is ever substituted for the
    quantum circuit: if PennyLane is missing a DependencyError is raised.
    """

    def __init__(self, qcfg: dict, entangle: bool = True):
        super().__init__()
        if not HAVE_PENNYLANE:
            raise DependencyError("PennyLane is required for the quantum experiments but could not be imported "
                                  "(%s). Install it with `pip install pennylane`. No classical substitute is used."
                                  % PENNYLANE_ERROR)
        self.n = int(qcfg["n_qubits"])
        self.L = int(qcfg["n_layers"])
        self.entangle = entangle
        self.weights = nn.Parameter(float(qcfg["init_std"]) * torch.randn(self.L, self.n, 2))
        # Trainable per-qubit input calibration: lets the circuit learn useful angle scales
        # instead of forcing every tanh embedding coordinate to use a fixed pi*z angle.
        self.input_scale = nn.Parameter(torch.ones(self.n))
        self.input_bias = nn.Parameter(torch.zeros(self.n))
        self.dev = qml.device(qcfg["device"], wires=self.n)
        self.qnode = qml.QNode(self._circuit, self.dev, interface="torch", diff_method=qcfg["diff_method"])
        self.out = nn.Linear(self.n, 1)

    def _circuit(self, angles, weights):
        n = self.n
        for i in range(n):
            qml.RY(angles[..., i], wires=i)                       # angle encoding: angle_i = pi * z_i
        for l in range(self.L):
            for i in range(n):
                qml.RY(weights[l, i, 0], wires=i)
                qml.RZ(weights[l, i, 1], wires=i)
            if self.entangle:
                for i in range(n):
                    qml.CNOT(wires=[i, (i + 1) % n])              # circular ring
        return [qml.expval(qml.PauliZ(i)) for i in range(n)]

    def quantum_features(self, angles):
        a = angles.double().cpu()
        res = self.qnode(a, self.weights.double().cpu())
        q = torch.stack(list(res), dim=-1) if isinstance(res, (list, tuple)) else res
        return q.to(angles.dtype).to(angles.device)

    def forward(self, z):
        calibrated = torch.tanh(z * self.input_scale + self.input_bias)
        angles = math.pi * calibrated
        return self.out(self.quantum_features(angles)).squeeze(-1)

    def draw_text(self) -> str:
        a = torch.zeros(self.n, dtype=torch.float64)
        return qml.draw(self.qnode)(a, self.weights.detach().double().cpu())


class EndToEnd(nn.Module):
    def __init__(self, enc: nn.Module, head: nn.Module):
        super().__init__()
        self.enc, self.head = enc, head

    def forward(self, x):
        return self.head(self.enc(x))


def make_head(kind: str, cfg: Cfg, seed: int) -> nn.Module:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        if kind == "linear":
            return LinearHead(cfg.tokens.embed_dim)
        if kind == "mlp":
            return MLPHead(cfg.tokens.embed_dim, cfg.model.mlp_hidden)
        if kind == "vqc":
            return QuantumHead(cfg.quantum, entangle=True)
        if kind == "vqc_nocnot":
            return QuantumHead(cfg.quantum, entangle=False)
    raise ValueError(kind)


def make_encoder(kind: str, n_freq: int, cfg: Cfg, seed: int) -> EEGEncoder:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return EEGEncoder(kind, n_freq, cfg)


def n_params(m: nn.Module) -> int:
    return int(sum(p.numel() for p in m.parameters() if p.requires_grad))


# =============================================================================
# TRAINING
# =============================================================================
def predict_logits(model: nn.Module, X: torch.Tensor, device, bs: int = 256) -> np.ndarray:
    model.eval()
    outs = []
    with torch.no_grad():
        for i in range(0, len(X), bs):
            outs.append(model(X[i:i + bs].to(device)).detach().cpu().double().numpy())
    return np.concatenate(outs) if outs else np.zeros(0)


def sigmoid_np(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))


def fit_nn(model: nn.Module, Xtr: torch.Tensor, ytr: np.ndarray, Xva: torch.Tensor, yva: np.ndarray, *,
           lr, weight_decay, max_epochs, patience, batch_size, clip, seed, pos_weight, device, name,
           param_groups=None, min_delta=1e-5, mixup_alpha=0.0) -> dict:
    """Mini-batch AdamW + BCEWithLogits; early stopping on VALIDATION loss; best checkpoint restored."""
    t0 = time.time()
    model.to(device)
    gen = torch.Generator().manual_seed(int(seed))
    opt = torch.optim.AdamW(param_groups if param_groups is not None else model.parameters(),
                            lr=lr, weight_decay=weight_decay)
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(pos_weight)).to(device))
    yt = torch.as_tensor(ytr, dtype=torch.float32)
    yv = torch.as_tensor(yva, dtype=torch.float32)
    n = len(Xtr)
    hist = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": [], "val_bal_acc": []}
    best, best_state, bad, best_ep = float("inf"), None, 0, -1
    params = [p for g in (param_groups or [{"params": model.parameters()}]) for p in g["params"]]
    for ep in range(int(max_epochs)):
        model.train()
        perm = torch.randperm(n, generator=gen)
        tl, tc, tn_ = 0.0, 0, 0
        for i in range(0, n, batch_size):
            idx = perm[i:i + batch_size]
            if len(idx) < 2 and n > 1:
                continue
            xb, yb = Xtr[idx].to(device), yt[idx].to(device)
            # Mixup is applied only within the training partition. Validation/test remain untouched.
            # It regularises the tiny recording dataset and is compatible with differentiable VQC heads.
            if mixup_alpha and len(xb) > 1:
                lam = float(np.random.beta(mixup_alpha, mixup_alpha))
                perm_b = torch.randperm(len(xb), device=device)
                xb_mix = lam * xb + (1.0 - lam) * xb[perm_b]
                yb_mix = lam * yb + (1.0 - lam) * yb[perm_b]
            else:
                xb_mix, yb_mix = xb, yb
            opt.zero_grad(set_to_none=True)
            logit = model(xb_mix)
            loss = crit(logit, yb_mix)
            loss.backward()
            if clip:
                torch.nn.utils.clip_grad_norm_(params, clip)
            opt.step()
            tl += float(loss.detach()) * len(idx)
            tc += int(((logit.detach() > 0).float() == (yb_mix >= 0.5).float()).sum())
            tn_ += len(idx)
        lv = predict_logits(model, Xva, device)
        vloss = float(crit(torch.as_tensor(lv, dtype=torch.float32).to(device), yv.to(device)))
        vpred = (lv > 0).astype(int)
        vacc = float(np.mean(vpred == yva))
        sens = np.mean(vpred[yva == 1] == 1) if (yva == 1).any() else np.nan
        spec = np.mean(vpred[yva == 0] == 0) if (yva == 0).any() else np.nan
        hist["train_loss"].append(tl / max(tn_, 1))
        hist["val_loss"].append(vloss)
        hist["train_acc"].append(tc / max(tn_, 1))
        hist["val_acc"].append(vacc)
        hist["val_bal_acc"].append(float(np.nanmean([sens, spec])))
        TLOG.info("[%s] epoch %3d/%d train_loss=%.4f val_loss=%.4f train_acc=%.3f val_acc=%.3f val_bal_acc=%.3f",
                  name, ep + 1, max_epochs, hist["train_loss"][-1], vloss, hist["train_acc"][-1], vacc,
                  hist["val_bal_acc"][-1])
        if vloss < best - min_delta:
            best, bad, best_ep = vloss, 0, ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                TLOG.info("[%s] early stopping at epoch %d (best epoch %d, val_loss %.4f)", name, ep + 1, best_ep + 1, best)
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    return {"history": hist, "best_epoch": best_ep + 1, "best_val_loss": best, "epochs_run": len(hist["val_loss"]),
            "seconds": time.time() - t0, "name": name}


def embed(enc: nn.Module, tokens: np.ndarray, device, bs: int = 128) -> np.ndarray:
    enc.eval()
    outs = []
    with torch.no_grad():
        for i in range(0, len(tokens), bs):
            outs.append(enc(torch.as_tensor(tokens[i:i + bs]).to(device)).cpu().numpy())
    return np.concatenate(outs).astype(np.float32) if outs else np.zeros((0, 6), np.float32)


def pos_weight_from(y: np.ndarray, use: bool) -> float:
    if not use:
        return 1.0
    npos = float((y == 1).sum())
    nneg = float((y == 0).sum())
    return nneg / max(npos, 1.0)


def val_logloss(y, p) -> float:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return float(log_loss(y, p, labels=[0, 1]))


def grid_product(grid: dict):
    keys = list(grid)
    out = [{}]
    for k in keys:
        out = [dict(o, **{k: v}) for o in out for v in grid[k]]
    return out


def fit_forest(Xtr, ytr, Xva, yva, seed, grid, balanced):
    best = (np.inf, None, None)
    for g in grid_product(grid):
        clf = RandomForestClassifier(random_state=seed, n_jobs=2, class_weight="balanced" if balanced else None, **g)
        clf.fit(Xtr, ytr)
        s = val_logloss(yva, clf.predict_proba(Xva)[:, 1])
        if s < best[0]:
            best = (s, clf, g)
    return best[1], best[2], best[0]


def fit_svc(Xtr, ytr, Xva, yva, seed, grid, balanced):
    best = (np.inf, None, None)
    for g in grid_product(grid):
        clf = SVC(probability=True, random_state=seed, class_weight="balanced" if balanced else None, **g)
        clf.fit(Xtr, ytr)
        s = val_logloss(yva, clf.predict_proba(Xva)[:, 1])
        if s < best[0]:
            best = (s, clf, g)
    return best[1], best[2], best[0]


def verify_quantum_gradients(cfg: Cfg, n_freq: int, device) -> dict:
    """Checks that gradients propagate through quantum weights, quantum input angles, the 6-D embedding and the
    encoder during end-to-end training (Transformer and Bi-LSTM)."""
    res = {}
    for kind in ("transformer", "bilstm"):
        torch.manual_seed(0)
        enc = EEGEncoder(kind, n_freq, cfg)
        head = QuantumHead(cfg.quantum, True)
        x = torch.randn(4, cfg.tokens.n_tokens, n_freq)
        z = enc(x)
        angles = math.pi * z
        angles.retain_grad()
        logits = head.out(head.quantum_features(angles)).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, torch.tensor([0., 1., 0., 1.]))
        loss.backward()
        gnorm = lambda p: float(p.grad.norm()) if p.grad is not None else 0.0
        res[kind] = {
            "quantum_weights_grad_norm": gnorm(head.weights),
            "quantum_input_angle_grad_norm": float(angles.grad.norm()) if angles.grad is not None else 0.0,
            "embedding_linear_grad_norm": gnorm(enc.embed[1].weight),
            "encoder_token_projection_grad_norm": gnorm(enc.proj.weight),
            "encoder_core_grad_norm": float(sum(p.grad.norm() ** 2 for p in enc.core.parameters() if p.grad is not None) ** 0.5),
            "output_layer_grad_norm": gnorm(head.out.weight),
            "all_nonzero": None,
        }
        res[kind]["all_nonzero"] = bool(all(v > 0 for k, v in res[kind].items() if k != "all_nonzero"))
    res["passed"] = all(res[k]["all_nonzero"] for k in ("transformer", "bilstm"))
    return res


# =============================================================================
# SYNTHETIC CORRUPTION (controlled robustness experiment - NOT real artefacts)
# =============================================================================
NOISE_LABELS = {"gaussian": "Gaussian noise", "baseline_drift": "Baseline drift",
                "emg_like": "EMG-like (synthetic)", "ocular_like": "Ocular-like (synthetic)"}


def gen_unit_noise(kind: str, n: int, fs: float, rng: np.random.Generator, nc: dict) -> np.ndarray:
    t = np.arange(n) / fs
    if kind == "gaussian":
        v = rng.standard_normal(n)
    elif kind == "baseline_drift":
        k = 4
        f = rng.uniform(nc["drift_freq_hz"][0], nc["drift_freq_hz"][1], k)
        ph = rng.uniform(0, 2 * np.pi, k)
        a = rng.uniform(0.5, 1.0, k)
        v = sum(a[i] * np.sin(2 * np.pi * f[i] * t + ph[i]) for i in range(k))
        v = v + rng.normal(0, 0.5) * (t - t.mean()) / (t[-1] + 1e-9)          # slow linear ramp
    elif kind == "emg_like":
        lo, hi = nc["emg_band_hz"]
        hi = min(hi, 0.95 * fs / 2)
        sos = sps.butter(4, [lo, hi], btype="band", fs=fs, output="sos")
        e = sps.sosfiltfilt(sos, rng.standard_normal(n))
        lp = sps.sosfiltfilt(sps.butter(2, 2.0, fs=fs, output="sos"), rng.standard_normal(n))
        env = 0.25 + 1.0 / (1.0 + np.exp(-3.0 * lp / (lp.std() + 1e-12)))      # bursty envelope
        v = e * env
    elif kind == "ocular_like":
        dur = n / fs
        nb = max(1, int(rng.poisson(nc["blink_rate_per_s"] * dur)))
        v = np.zeros(n)
        for _ in range(nb):
            t0 = rng.uniform(0.0, dur)
            w = nc["blink_width_s"] * rng.uniform(0.8, 1.2)
            v += rng.uniform(0.6, 1.4) * np.exp(-0.5 * ((t - t0) / (w / 2.5)) ** 2)
        lo, hi = nc["ocular_band_hz"]
        sos = sps.butter(2, [lo, hi], btype="band", fs=fs, output="sos")
        v = v / (v.std() + 1e-12) + 0.3 * sps.sosfiltfilt(sos, rng.standard_normal(n)) / 1.0
    else:
        raise ValueError(kind)
    v = v - v.mean()
    return v / (v.std() + 1e-12)


def corrupt_signal(x_raw: np.ndarray, ref_power: float, kind: str, snr_db: float, rec_id: str, fs: float,
                   nc: dict) -> np.ndarray:
    """Deterministic: the generator seed depends only on (noise seed, recording, type, SNR), so the same
    corruption is applied identically for every model / fold / experiment seed."""
    rng = np.random.default_rng(zlib.crc32(("%s|%s|%s|%s" % (nc["seed"], rec_id, kind, snr_db)).encode()))
    noise = gen_unit_noise(kind, len(x_raw), fs, rng, nc)
    pn = ref_power / (10.0 ** (snr_db / 10.0))
    return x_raw + noise * math.sqrt(pn)


# =============================================================================
# EXPERIMENT CONTEXT: representation building
# =============================================================================
class RowView:
    """Lazy row subset of a (memmap) array supporting slicing, so no 500 MB copy is made."""

    def __init__(self, arr, idx):
        self.arr, self.idx = arr, np.asarray(idx)

    def __len__(self):
        return len(self.idx)

    def __getitem__(self, sl):
        return np.asarray(self.arr[self.idx[sl]])


class Ctx:
    pass


def make_dirs(root: Path) -> dict:
    sub = ["logs", "config", "data", "checkpoints/classical_heads", "checkpoints/quantum_heads",
           "checkpoints/encoders", "checkpoints/feature_models", "metrics", "plots", "diagrams", "reports", "cache"]
    d = {"root": root, "checkpoints": root / "checkpoints"}
    for s in sub:
        (root / s).mkdir(parents=True, exist_ok=True)
        d[s.split("/")[-1] if s.startswith("checkpoints/") else s] = root / s
    return d


def build_representation(ctx: Ctx) -> None:
    cfg = ctx.cfg
    fs = cfg.data.fs
    win = int(round(cfg.window.seconds * fs))
    hop = int(round(win * (1.0 - cfg.window.overlap)))
    ctx.win, ctx.hop = win, hop
    rows, wins = [], []
    rec_rows = []
    for ridx, r in ctx.man_used.reset_index(drop=True).iterrows():
        W, starts, left = segment_signal(ctx.filt[r.rec_id], win, hop)
        for j, (w, s) in enumerate(zip(W, starts)):
            wins.append(w)
            rows.append(dict(rec_idx=ridx, rec_id=r.rec_id, win_idx=j, start=int(s), label=int(r.label),
                             activity=r.activity, group=r.activity_group, class_name=r.class_name))
        rec_rows.append(dict(rec_idx=ridx, rec_id=r.rec_id, n_windows=len(W), leftover_samples=left,
                             n_samples_used=len(ctx.filt[r.rec_id])))
        if left:
            LOG.debug("%s: %d trailing samples form an incomplete window and are excluded", r.rec_id, left)
    ctx.win_df = pd.DataFrame(rows)
    base = ctx.man_used.reset_index(drop=True)
    base.insert(0, "rec_idx", np.arange(len(base)))
    ctx.rec_df = base.merge(pd.DataFrame(rec_rows).drop(columns=["rec_id"]), on="rec_idx", how="left")
    ctx.rec_df["wosg_window"] = ctx.rec_df.rec_id.map(lambda r: ctx.wosg_info[r].get("window"))
    ctx.rec_df["wosg_polyorder"] = ctx.rec_df.rec_id.map(lambda r: ctx.wosg_info[r].get("polyorder"))
    W = np.stack(wins)
    LOG.info("Segmentation: %d recordings -> %d windows of %d samples (hop %d); leftover samples per recording: %s",
             len(ctx.rec_df), len(W), win, hop, dict(Counter(ctx.rec_df.leftover_samples)))
    freqs = np.linspace(cfg.gwst.fmin, cfg.gwst.fmax, int(cfg.gwst.n_freq))
    ctx.gwst = GWST(win, fs, freqs)
    ctx.n_freq = len(freqs)
    cache = ctx.dirs["cache"] / "gwst_magnitude.npy"
    ctx.Smag = np.lib.format.open_memmap(cache, mode="w+", dtype=np.float32, shape=(len(W), ctx.n_freq, win))
    mean_mag, feats = np.zeros((len(W), ctx.n_freq), np.float32), []
    B = int(cfg.gwst.batch)
    t0 = time.time()
    for i in range(0, len(W), B):
        S = ctx.gwst.magnitude(W[i:i + B])
        ctx.Smag[i:i + B] = S
        mean_mag[i:i + B] = S.mean(axis=2)
        feats.append(l1_entropy_features(S, cfg.features.entropy_bins))
    ctx.Smag.flush()
    ctx.mean_mag = mean_mag
    ctx.feats = np.concatenate(feats)
    LOG.info("GWST + features for %d windows in %.1f s; GWST shape per window = [%d freq x %d time]",
             len(W), time.time() - t0, ctx.n_freq, win)
    assert ctx.feats.shape[1] == 2 * ctx.n_freq, "feature dimension mismatch"
    if ctx.n_freq == 225:
        assert ctx.feats.shape[1] == 450, "expected 450-D feature vectors"
    assert np.isfinite(ctx.feats).all(), "non-finite features"
    ctx.windows_raw = W
    np.save(ctx.dirs["data"] / "feature_matrix.npy", ctx.feats)
    np.save(ctx.dirs["data"] / "feature_labels.npy", ctx.win_df.label.values)
    ctx.win_df.to_csv(ctx.dirs["data"] / "window_metadata.csv", index=False)
    cols = [c for c in ctx.rec_df.columns if c not in ("sha1",)]
    ctx.rec_df[cols].to_csv(ctx.dirs["data"] / "recording_metadata.csv", index=False)
    cnt = ctx.win_df.groupby(["class_name", "activity"]).agg(recordings=("rec_idx", "nunique"), windows=("rec_idx", "size"))
    cnt.reset_index().to_csv(ctx.dirs["data"] / "recordings_windows_per_class_activity.csv", index=False)
    wosg_tbl = pd.DataFrame([dict(rec_id=k, **{kk: vv for kk, vv in v.items()}) for k, v in ctx.wosg_info.items()])
    wosg_tbl.to_csv(ctx.dirs["config"] / "wosg_per_recording_parameters.csv", index=False)
    # token dimensions
    tp = cfg.tokens
    exp_T = ctx.win // tp.pool
    if exp_T != tp.n_tokens:
        raise ValueError("GWST time axis %d / pool %d = %d tokens != configured %d" % (ctx.win, tp.pool, exp_T, tp.n_tokens))
    ctx.token_shape = (tp.n_tokens, ctx.n_freq)
    LOG.info("Temporal token tensor per window: [%d, %d] -> Linear(%d, %d) -> [%d, %d]",
             tp.n_tokens, ctx.n_freq, ctx.n_freq, tp.token_dim, tp.n_tokens, tp.token_dim)
    eligible = ctx.audit["eligible_activities_both_classes"]
    ctx.eligible = eligible
    ctx.noise_cache = {}


def windows_to_inputs(ctx: Ctx, windows: np.ndarray, scaler: TokenScaler, chunk: int = 48):
    feats, toks = [], []
    for i in range(0, len(windows), chunk):
        S = ctx.gwst.magnitude(windows[i:i + chunk])
        feats.append(l1_entropy_features(S, ctx.cfg.features.entropy_bins))
        toks.append(scaler.transform(S))
    return np.concatenate(feats), np.concatenate(toks)


# =============================================================================
# FITTING ALL MODELS FOR ONE TRAIN/VALIDATION PARTITION
# =============================================================================
def active_experiments(cfg: Cfg, restrict=None) -> list[str]:
    ids = []
    for eid, e in EXPERIMENTS.items():
        if restrict not in (None, "all") and eid not in restrict:
            continue
        if e["family"] == "feature" and not cfg.run.run_baselines:
            continue
        if e["family"] in ("head", "finetune") and not cfg.run.run_encoders:
            continue
        if e.get("head") in QUANTUM_HEADS and not cfg.run.run_quantum:
            continue
        if e["family"] == "finetune" and not cfg.run.run_finetune:
            continue
        ids.append(eid)
    return ids


def lr_grid(cfg: Cfg, kind: str):
    t = cfg.train
    if kind == "encoder":
        return t.encoder_lr_grid or [t.lr_encoder]
    if kind in ("vqc", "vqc_nocnot"):
        return t.head_lr_grid or [t.lr_quantum]
    return t.head_lr_grid or [t.lr_head]


def fit_bundle(ctx: Ctx, seed: int, tr: np.ndarray, va: np.ndarray, ids: list[str], tag: str,
               save_ckpt: bool = False) -> dict:
    cfg, dev = ctx.cfg, ctx.device
    wd = ctx.win_df
    ytr, yva = wd.label.values[tr], wd.label.values[va]
    sc = TokenScaler(cfg.tokens.n_tokens, cfg.tokens.pool)
    sc.fit_a0(ctx.mean_mag[tr])
    tok_tr_raw = sc.raw_tokens(RowView(ctx.Smag, tr))
    sc.fit_standardizer(tok_tr_raw)
    tok_tr = sc.standardize(tok_tr_raw)
    del tok_tr_raw
    tok_va = sc.transform(RowView(ctx.Smag, va))
    pw = pos_weight_from(ytr, cfg.train.use_class_weights)
    B = {"scaler": sc, "feat_models": {}, "enc": {}, "ft": {}, "fit_info": [], "histories": [], "a0": sc.a0}
    LOG.info("[%s] seed=%d train: %d windows (%d rec) | val: %d windows (%d rec) | a0=%.5g | pos_weight=%.2f",
             tag, seed, len(tr), wd.rec_idx.values[tr].tolist().__len__() and len(set(wd.rec_idx.values[tr])),
             len(va), len(set(wd.rec_idx.values[va])), sc.a0, pw)

    def add_info(eid, res, np_, extra=None):
        d = dict(tag=tag, seed=seed, model=eid, epochs_run=res.get("epochs_run"), best_epoch=res.get("best_epoch"),
                 best_val_loss=res.get("best_val_loss"), seconds=res.get("seconds"), n_params=np_)
        d.update(extra or {})
        B["fit_info"].append(d)

    # ---------------- feature baselines (E1-E3) ----------------
    fids = [i for i in ids if EXPERIMENTS[i]["family"] == "feature"]
    if fids:
        Ftr, Fva = ctx.feats[tr], ctx.feats[va]
        ss = StandardScaler().fit(Ftr)
        Xtr, Xva = ss.transform(Ftr), ss.transform(Fva)
        bal = cfg.train.use_class_weights
        if "E1" in fids:
            t0 = time.time()
            clf, g, s = fit_forest(Xtr, ytr, Xva, yva, seed, cfg.classical.rf_grid, bal)
            B["feat_models"]["E1"] = (lambda Fm, c=clf, s_=ss: c.predict_proba(s_.transform(Fm))[:, 1])
            add_info("E1", {"seconds": time.time() - t0, "best_val_loss": s}, None, {"hyper": str(g)})
            if save_ckpt:
                joblib.dump(clf, ctx.dirs["feature_models"] / ("E1_rf_%s.joblib" % tag))
        if "E2" in fids:
            t0 = time.time()
            clf, g, s = fit_svc(Xtr, ytr, Xva, yva, seed, cfg.classical.svm_grid, bal)
            B["feat_models"]["E2"] = (lambda Fm, c=clf, s_=ss: c.predict_proba(s_.transform(Fm))[:, 1])
            add_info("E2", {"seconds": time.time() - t0, "best_val_loss": s}, None, {"hyper": str(g)})
            if save_ckpt:
                joblib.dump(clf, ctx.dirs["feature_models"] / ("E2_svm_%s.joblib" % tag))
        if "E3" in fids:
            t0 = time.time()
            mi = mutual_info_classif(Xtr, ytr, random_state=seed)        # fitted on TRAINING partition only
            order = np.argsort(-mi)
            best = (np.inf, None, None, None)
            for k in [k for k in cfg.classical.mi_k_grid if k <= Xtr.shape[1]]:
                sel = order[:k]
                clf, g, s = fit_forest(Xtr[:, sel], ytr, Xva[:, sel], yva, seed, cfg.classical.rf_grid, bal)
                if s < best[0]:
                    best = (s, clf, g, sel)
            B["feat_models"]["E3"] = (lambda Fm, c=best[1], s_=ss, sel=best[3]: c.predict_proba(s_.transform(Fm)[:, sel])[:, 1])
            add_info("E3", {"seconds": time.time() - t0, "best_val_loss": best[0]}, None,
                     {"hyper": str(best[2]), "mi_k": int(len(best[3]))})
            if save_ckpt:
                joblib.dump({"model": best[1], "selected": best[3]}, ctx.dirs["feature_models"] / ("E3_mi_rf_%s.joblib" % tag))
        LOG.info("[%s] feature baselines fitted: %s", tag, fids)

    # ---------------- encoders + matched heads (E4-E12, fine-tuned) ----------------
    for enc_kind in ("transformer", "bilstm"):
        eids = [i for i in ids if EXPERIMENTS[i]["family"] in ("head", "finetune") and EXPERIMENTS[i]["enc"] == enc_kind]
        if not eids:
            continue
        name = "%s|%s|pretrain" % (enc_kind, tag)
        Xtr_t, Xva_t = torch.as_tensor(tok_tr), torch.as_tensor(tok_va)
        best_fit, best_model = None, None
        for lr in lr_grid(cfg, "encoder"):
            pre_head = make_head(cfg.model.encoder_pretrain_head, cfg, seed)
            m = EndToEnd(make_encoder(enc_kind, ctx.n_freq, cfg, seed), pre_head)
            res = fit_nn(m, Xtr_t, ytr, Xva_t, yva, lr=lr, weight_decay=cfg.train.weight_decay,
                         max_epochs=cfg.train.max_epochs, patience=cfg.train.patience,
                         batch_size=cfg.train.batch_size, clip=cfg.train.grad_clip, seed=seed, pos_weight=pw,
                         device=dev, name=name + "|lr%g" % lr, min_delta=cfg.train.min_delta, mixup_alpha=cfg.train.mixup_alpha)
            if best_fit is None or res["best_val_loss"] < best_fit["best_val_loss"]:
                best_fit, best_model, best_fit["lr"] = res, m, lr
        enc = best_model.enc
        enc_state = {k: v.detach().cpu().clone() for k, v in enc.state_dict().items()}
        B["histories"].append(dict(kind=enc_kind, tag=tag, seed=seed, stage="pretrain", **best_fit["history"]))
        add_info("pretrain_" + enc_kind, best_fit, n_params(best_model.enc), {"lr": best_fit["lr"]})
        LOG.info("[%s] %s encoder pre-trained: epochs=%d best_epoch=%d val_loss=%.4f (%.1fs)", tag, enc_kind,
                 best_fit["epochs_run"], best_fit["best_epoch"], best_fit["best_val_loss"], best_fit["seconds"])
        if save_ckpt:
            ck = ctx.dirs["encoders"] / ("%s_%s.pt" % (enc_kind, tag))
            torch.save({"state_dict": enc_state, "kind": enc_kind, "n_freq": ctx.n_freq, "val_loss": best_fit["best_val_loss"],
                        "a0": sc.a0, "mu": sc.mu, "sd": sc.sd}, ck)
            if best_fit["best_val_loss"] < ctx.best_enc.get(enc_kind, (np.inf, None))[0]:
                ctx.best_enc[enc_kind] = (best_fit["best_val_loss"], ck)
        # ---- frozen encoder: identical embeddings for every head ----
        for p in enc.parameters():
            p.requires_grad_(False)
        enc.to(dev).eval()
        Ztr, Zva = embed(enc, tok_tr, dev), embed(enc, tok_va, dev)
        Ztr_t, Zva_t = torch.as_tensor(Ztr), torch.as_tensor(Zva)
        heads = {}
        for eid in [i for i in eids if EXPERIMENTS[i]["family"] == "head"]:
            hk = EXPERIMENTS[eid]["head"]
            if hk == "rbf_svm":
                t0 = time.time()
                clf, g, s = fit_svc(Ztr, ytr, Zva, yva, seed, {"kernel": ["rbf"], **cfg.classical.rbf_head_grid},
                                    cfg.train.use_class_weights)
                heads[eid] = (lambda Z, c=clf: c.predict_proba(Z)[:, 1])
                add_info(eid, {"seconds": time.time() - t0, "best_val_loss": s}, None, {"hyper": str(g)})
                if save_ckpt:
                    joblib.dump(clf, ctx.dirs["classical_heads"] / ("%s_%s_rbfsvm_%s.joblib" % (eid, enc_kind, tag)))
                continue
            best_h = None
            for lr in lr_grid(cfg, hk):
                head = make_head(hk, cfg, seed)
                res = fit_nn(head, Ztr_t, ytr, Zva_t, yva, lr=lr, weight_decay=cfg.train.weight_decay,
                             max_epochs=cfg.train.head_max_epochs, patience=cfg.train.head_patience,
                             batch_size=cfg.train.batch_size, clip=cfg.train.grad_clip, seed=seed, pos_weight=pw,
                             device=torch.device("cpu"), name="%s|%s|%s|%s|lr%g" % (eid, enc_kind, hk, tag, lr),
                             min_delta=cfg.train.min_delta, mixup_alpha=cfg.train.mixup_alpha)
                if best_h is None or res["best_val_loss"] < best_h[1]["best_val_loss"]:
                    best_h = (head, res, lr)
            head, res, lr = best_h
            heads[eid] = (lambda Z, h=head: sigmoid_np(predict_logits(h, torch.as_tensor(Z), torch.device("cpu"))))
            add_info(eid, res, n_params(head), {"lr": lr})
            LOG.info("[%s] %s head=%s: epochs=%d best_epoch=%d val_loss=%.4f params=%d (%.1fs)", tag, eid, hk,
                     res["epochs_run"], res["best_epoch"], res["best_val_loss"], n_params(head), res["seconds"])
            if save_ckpt:
                sub = "quantum_heads" if hk in QUANTUM_HEADS else "classical_heads"
                torch.save(head.state_dict(), ctx.dirs[sub] / ("%s_%s_%s_%s.pt" % (eid, enc_kind, hk, tag)))
        B["enc"][enc_kind] = {"encoder": enc, "heads": heads}
        # ---- separate end-to-end fine-tuning comparison ----
        for eid in [i for i in eids if EXPERIMENTS[i]["family"] == "finetune"]:
            hk = EXPERIMENTS[eid]["head"]
            best_f = None
            for lr_h in lr_grid(cfg, hk):
                enc2 = make_encoder(enc_kind, ctx.n_freq, cfg, seed)
                enc2.load_state_dict(enc_state)
                head = make_head(hk, cfg, seed)
                m = EndToEnd(enc2, head)
                groups = [{"params": list(enc2.parameters()), "lr": cfg.train.lr_finetune_encoder},
                          {"params": list(head.parameters()), "lr": lr_h}]
                res = fit_nn(m, Xtr_t, ytr, Xva_t, yva, lr=lr_h, weight_decay=cfg.train.weight_decay,
                             max_epochs=cfg.train.ft_max_epochs, patience=cfg.train.ft_patience,
                             batch_size=cfg.train.batch_size, clip=cfg.train.grad_clip, seed=seed, pos_weight=pw,
                             device=dev, name="%s|%s|%s|%s" % (eid, enc_kind, hk, tag), param_groups=groups,
                             min_delta=cfg.train.min_delta, mixup_alpha=cfg.train.mixup_alpha)
                if best_f is None or res["best_val_loss"] < best_f[1]["best_val_loss"]:
                    best_f = (m, res, lr_h)
            m, res, lr_h = best_f
            B["ft"][eid] = (lambda T, mm=m: sigmoid_np(predict_logits(mm, torch.as_tensor(T), dev)))
            add_info(eid, res, n_params(m), {"lr": lr_h})
            LOG.info("[%s] %s fine-tuned: epochs=%d val_loss=%.4f params=%d (%.1fs)", tag, eid, res["epochs_run"],
                     res["best_val_loss"], n_params(m), res["seconds"])
    return B


def predict_inputs(ctx: Ctx, B: dict, feats: np.ndarray, tokens: np.ndarray) -> dict:
    out = {}
    for eid, fn in B["feat_models"].items():
        out[eid] = np.asarray(fn(feats), dtype=float)
    for enc_kind, d in B["enc"].items():
        Z = embed(d["encoder"], tokens, ctx.device)
        for eid, fn in d["heads"].items():
            out[eid] = np.asarray(fn(Z), dtype=float)
    for eid, fn in B["ft"].items():
        out[eid] = np.asarray(fn(tokens), dtype=float)
    return out


def frame_from_preds(ctx: Ctx, preds: dict, win_idx: np.ndarray, **meta) -> pd.DataFrame:
    wd = ctx.win_df.iloc[win_idx]
    parts = []
    for eid, p in preds.items():
        d = pd.DataFrame({"model": eid, "rec_idx": wd.rec_idx.values, "rec_id": wd.rec_id.values,
                          "win_idx": wd.win_idx.values, "label": wd.label.values, "prob": p})
        for k, v in meta.items():
            d[k] = v
        parts.append(d)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def thresholds_from_val(ctx: Ctx, preds_val: dict, va: np.ndarray) -> dict:
    wd = ctx.win_df.iloc[va]
    thr = {}
    for eid, p in preds_val.items():
        tw = select_threshold(wd.label.values, p)
        rec = pd.DataFrame({"r": wd.rec_idx.values, "y": wd.label.values, "p": p}).groupby("r").agg(y=("y", "first"), p=("p", "mean"))
        tr_ = select_threshold(rec.y.values, rec.p.values)
        thr[eid] = (tw, tr_)
    return thr


def attach_thresholds(df: pd.DataFrame, thr: dict) -> pd.DataFrame:
    df["thr_w"] = df.model.map(lambda m: thr[m][0])
    df["thr_r"] = df.model.map(lambda m: thr[m][1])
    return df


def corrupted_windows(ctx: Ctx, rec_idx: int, kind: str, snr: float) -> np.ndarray:
    key = (rec_idx, kind, snr)
    if key in ctx.noise_cache:
        return ctx.noise_cache[key]
    r = ctx.rec_df.iloc[rec_idx]
    xr = ctx.raw_used[r.rec_id]
    ref = ctx.cfg.noise.snr_reference
    ref_x = ctx.filt[r.rec_id] if ref == "filtered" else xr
    power = float(np.var(ref_x))
    xc = corrupt_signal(xr, power, kind, snr, r.rec_id, ctx.cfg.data.fs, ctx.cfg.noise)
    y, _ = wosg_filter(xc, ctx.cfg.data.fs, ctx.cfg.wosg)            # the SAME WOSG stage is applied
    W, _, _ = segment_signal(y, ctx.win, ctx.hop)
    ctx.noise_cache[key] = W
    return W


def evaluate_noise(ctx: Ctx, B: dict, te: np.ndarray, thr: dict, seed: int, fold: int) -> list[pd.DataFrame]:
    """Already-trained models are evaluated on corrupted TEST recordings only (no retraining/tuning)."""
    cfg = ctx.cfg
    wd = ctx.win_df.iloc[te]
    rec_order = list(dict.fromkeys(wd.rec_idx.tolist()))
    frames = []
    for kind in cfg.noise.types:
        for snr in cfg.noise.snr_db:
            t0 = time.time()
            Ws = []
            for ridx in rec_order:
                Wc = corrupted_windows(ctx, ridx, kind, float(snr))
                n_expected = int((wd.rec_idx.values == ridx).sum())
                assert len(Wc) == n_expected, "corrupted window count mismatch"
                Ws.append(Wc)
            feats, toks = windows_to_inputs(ctx, np.concatenate(Ws), B["scaler"])
            order_idx = np.concatenate([te[wd.rec_idx.values == r] for r in rec_order])
            preds = predict_inputs(ctx, B, feats, toks)
            d = frame_from_preds(ctx, preds, order_idx, seed=seed, fold=fold, split="test", condition="%s@%gdB" % (kind, snr),
                                 noise_type=kind, snr_db=float(snr))
            frames.append(attach_thresholds(d, thr))
            LOG.info("  noise %s @ %g dB evaluated (%.1fs)", kind, snr, time.time() - t0)
    return frames


# =============================================================================
# OUTER CROSS-VALIDATION
# =============================================================================
def run_outer_cv(ctx: Ctx) -> None:
    cfg = ctx.cfg
    ids = active_experiments(cfg)
    LOG.info("Active experiments (%d): %s", len(ids), ids)
    pool = np.ones(len(ctx.win_df), bool)
    if cfg.data.main_scope == "paired":
        pool = ctx.win_df.activity.isin(ctx.eligible).values
        LOG.info("main_scope=paired -> %d windows from activities present in both classes", pool.sum())
    ctx.pool_mask = pool
    noise_seeds = cfg.noise.seeds if cfg.noise.seeds is not None else cfg.run.seeds
    assign_rows = []
    for seed in cfg.run.seeds:
        set_seed(seed)
        folds = outer_folds(ctx.win_df, pool, cfg.run.n_folds, seed)
        for f, (tr_all, te) in enumerate(folds):
            if cfg.run.max_folds is not None and f >= cfg.run.max_folds:
                break
            t_fold = time.time()
            LOG.info("-" * 78)
            LOG.info("OUTER CV  seed=%d  fold=%d/%d", seed, f + 1, cfg.run.n_folds)
            tr, va = inner_split(ctx.win_df, tr_all, cfg.cv.inner_val_splits, seed * 100 + f)
            for role, idx in (("train", tr), ("validation", va), ("test", te)):
                for ridx in sorted(set(ctx.win_df.rec_idx.values[idx])):
                    rr = ctx.rec_df.iloc[ridx]
                    assign_rows.append(dict(seed=seed, fold=f, role=role, rec_id=rr.rec_id, label=int(rr.label),
                                            class_name=rr.class_name, activity=rr.activity,
                                            n_windows=int((ctx.win_df.rec_idx.values[idx] == ridx).sum())))
            for role, idx in (("train", tr), ("validation", va), ("test", te)):
                ps = partition_summary(ctx.win_df, set(ctx.win_df.rec_idx.values[idx]))
                LOG.info("  %-10s %s", role, {k: v for k, v in ps.items() if k != "activity_counts"})
            tag = "s%d_f%d" % (seed, f)
            B = fit_bundle(ctx, seed, tr, va, ids, tag, save_ckpt=True)
            ctx.fit_rows.extend(B["fit_info"])
            ctx.histories.extend(B["histories"])
            sc = B["scaler"]
            tok_va = sc.transform(RowView(ctx.Smag, va))
            pv = predict_inputs(ctx, B, ctx.feats[va], tok_va)
            thr = thresholds_from_val(ctx, pv, va)
            for m, (tw, trr) in thr.items():
                LOG.info("  threshold %-9s window=%.3f recording=%.3f", m, tw, trr)
            fv = attach_thresholds(frame_from_preds(ctx, pv, va, seed=seed, fold=f, split="val", condition="clean",
                                                    noise_type="", snr_db=np.nan), thr)
            tok_te = sc.transform(RowView(ctx.Smag, te))
            pt = predict_inputs(ctx, B, ctx.feats[te], tok_te)
            ft = attach_thresholds(frame_from_preds(ctx, pt, te, seed=seed, fold=f, split="test", condition="clean",
                                                    noise_type="", snr_db=np.nan), thr)
            ctx.frames.extend([fv, ft])
            quick = recording_metrics_table(recording_frame(ft, ["seed", "fold", "model"]), ["seed", "fold", "model"])
            for _, r in quick.iterrows():
                LOG.info("  [test, recording-level] %-9s acc=%s bal_acc=%s", r.model, fmt_ms(r.accuracy, None),
                         fmt_ms(r.balanced_accuracy, None))
            if cfg.run.run_noise and seed in noise_seeds:
                ctx.frames.extend(evaluate_noise(ctx, B, te, thr, seed, f))
            LOG.info("fold finished in %.1f s", time.time() - t_fold)
            del B
    ctx.assignments = pd.DataFrame(assign_rows)
    ctx.assignments.to_csv(ctx.dirs["config"] / "fold_assignments.csv", index=False)


# =============================================================================
# LEAVE-ONE-ACTIVITY-OUT
# =============================================================================
def run_loao(ctx: Ctx) -> None:
    cfg = ctx.cfg
    ids = active_experiments(cfg, restrict=cfg.loao.models)
    ids = [i for i in ids if EXPERIMENTS[i]["family"] != "finetune"] if cfg.loao.models == "all" else ids
    seeds = cfg.loao.seeds if cfg.loao.seeds is not None else cfg.run.seeds
    acts = list(ctx.eligible)
    if cfg.loao.get("max_activities"):
        acts = acts[: cfg.loao.max_activities]
    LOG.info("LOAO: held-out activities %s | models %s | seeds %s", acts, ids, seeds)
    wd = ctx.win_df
    rows = []
    for seed in seeds:
        for a in acts:
            set_seed(seed)
            t0 = time.time()
            train_acts = [x for x in ctx.eligible if x != a]
            tr_all = np.flatnonzero(wd.activity.isin(train_acts).values)
            te = np.flatnonzero((wd.activity == a).values)
            assert not (set(wd.rec_idx.values[tr_all]) & set(wd.rec_idx.values[te]))
            tr, va = inner_split(wd, tr_all, cfg.cv.inner_val_splits, seed * 1000 + zlib.crc32(a.encode()) % 997)
            assert not (set(wd.activity.values[tr]) | set(wd.activity.values[va])) & {a}
            tag = "loao_%s_s%d" % (a.replace(" ", "_"), seed)
            LOG.info("-" * 78)
            LOG.info("LOAO seed=%d held-out=%s | train acts=%s", seed, a, train_acts)
            B = fit_bundle(ctx, seed, tr, va, ids, tag, save_ckpt=False)
            ctx.fit_rows.extend(B["fit_info"])
            sc = B["scaler"]
            pv = predict_inputs(ctx, B, ctx.feats[va], sc.transform(RowView(ctx.Smag, va)))
            thr = thresholds_from_val(ctx, pv, va)
            pt = predict_inputs(ctx, B, ctx.feats[te], sc.transform(RowView(ctx.Smag, te)))
            ft = attach_thresholds(frame_from_preds(ctx, pt, te, seed=seed, fold=-1, split="test", condition="clean",
                                                    noise_type="", snr_db=np.nan, heldout=a), thr)
            ctx.loao_frames.append(ft)
            ctx.loao_meta.append(dict(seed=seed, heldout=a, train_activities=";".join(train_acts),
                                      n_train_rec=len(set(wd.rec_idx.values[tr])), n_val_rec=len(set(wd.rec_idx.values[va])),
                                      n_test_rec=len(set(wd.rec_idx.values[te])),
                                      test_healthy=len(set(wd.rec_idx.values[te][wd.label.values[te] == 0])),
                                      test_epilepsy=len(set(wd.rec_idx.values[te][wd.label.values[te] == 1]))))
            LOG.info("LOAO %s done in %.1f s", a, time.time() - t0)
            del B


# =============================================================================
# AGGREGATION: window / recording level tables
# =============================================================================
def recording_frame(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Window probabilities -> ONE recording-level probability (mean) and decision (validation threshold)."""
    g = df.groupby(keys + ["rec_idx", "rec_id"], sort=False)
    r = g.agg(label=("label", "first"), mean_prob=("prob", "mean"), n_windows=("prob", "size"),
              thr_r=("thr_r", "first"), thr_w=("thr_w", "first")).reset_index()
    r["pred"] = (r.mean_prob >= r.thr_r).astype(int)
    r["correct"] = (r.pred == r.label).astype(int)
    return r


def recording_metrics_table(rec: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for k, g in rec.groupby(keys, sort=False):
        k = k if isinstance(k, tuple) else (k,)
        m = compute_metrics(g.label.values, g.mean_prob.values, g.pred.values)
        rows.append(dict(zip(keys, k), **m))
    return pd.DataFrame(rows)


def window_metrics_table(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(keys, sort=False):
        k = k if isinstance(k, tuple) else (k,)
        pred = (g.prob.values >= g.thr_w.values).astype(int)
        m = compute_metrics(g.label.values, g.prob.values, pred)
        rows.append(dict(zip(keys, k), **m))
    return pd.DataFrame(rows)


def summarize(fold_df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """mean / std / #valid folds for every metric (NaN-aware: unavailable metrics are never imputed)."""
    rows = []
    for k, g in fold_df.groupby(group_cols, sort=False):
        k = k if isinstance(k, tuple) else (k,)
        d = dict(zip(group_cols, k))
        d["n_folds_evaluated"] = int(len(g))
        d["n_seeds"] = int(g.seed.nunique()) if "seed" in g else 1
        for m in METRIC_COLS:
            v = g[m].values.astype(float)
            ok = np.isfinite(v)
            d[m + "_mean"] = float(v[ok].mean()) if ok.any() else np.nan
            d[m + "_std"] = float(v[ok].std(ddof=1)) if ok.sum() > 1 else np.nan
            d[m + "_n_valid"] = int(ok.sum())
        rows.append(d)
    return pd.DataFrame(rows)


def bootstrap_models(rec_pooled: pd.DataFrame, models: list[str], n_boot: int, ci: float, seed: int):
    """Recording-level bootstrap (resample COMPLETE recordings; the same resample is applied to every seed and
    the metric is averaged over seeds). Returns (ci_df, arrays) where arrays[model] = (y, pred[S,R], prob[S,R])."""
    seeds = sorted(rec_pooled.seed.unique())
    common = None
    for s in seeds:
        r = set(rec_pooled[rec_pooled.seed == s].rec_idx)
        common = r if common is None else common & r
    common = sorted(common)
    arrays, rows = {}, []
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(common), size=(n_boot, len(common)))
    for m in models:
        sub = rec_pooled[(rec_pooled.model == m) & rec_pooled.rec_idx.isin(common)]
        if sub.empty:
            continue
        y = sub[sub.seed == seeds[0]].sort_values("rec_idx").label.values
        pred = np.stack([sub[sub.seed == s].sort_values("rec_idx").pred.values for s in seeds])
        prob = np.stack([sub[sub.seed == s].sort_values("rec_idx").mean_prob.values for s in seeds])
        arrays[m] = (y, pred, prob)
        dist = {}
        for si in range(len(seeds)):
            bm = fast_batch_metrics(y[idx], pred[si][idx], prob[si][idx])
            for k, v in bm.items():
                dist.setdefault(k, []).append(v)
        row = {"model": m, "n_recordings": len(common), "n_seeds": len(seeds), "n_bootstrap": n_boot}
        for k, v in dist.items():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                avg = np.nanmean(np.stack(v), axis=0)
            avg = avg[np.isfinite(avg)]
            lo, hi = (np.percentile(avg, [100 * (1 - ci) / 2, 100 * (1 + ci) / 2]) if len(avg) > 10 else (np.nan, np.nan))
            row[k + "_ci_low"], row[k + "_ci_high"] = float(lo), float(hi)
        rows.append(row)
    return pd.DataFrame(rows), arrays, idx


def paired_comparisons(arrays: dict, idx: np.ndarray, pairs: list[tuple[str, str]], ci: float) -> pd.DataFrame:
    rows = []
    for a, b in pairs:
        if a not in arrays or b not in arrays:
            continue
        ya, pa, qa = arrays[a]
        _, pb, qb = arrays[b]
        S = pa.shape[0]
        for metric in ("balanced_accuracy", "accuracy", "roc_auc"):
            d = []
            for si in range(S):
                ma = fast_batch_metrics(ya[idx], pa[si][idx], qa[si][idx])[metric]
                mb = fast_batch_metrics(ya[idx], pb[si][idx], qb[si][idx])[metric]
                d.append(ma - mb)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dd = np.nanmean(np.stack(d), axis=0)
            dd = dd[np.isfinite(dd)]
            point = []
            for si in range(S):
                m0 = fast_batch_metrics(ya[None], pa[si][None], qa[si][None])[metric][0]
                m1 = fast_batch_metrics(ya[None], pb[si][None], qb[si][None])[metric][0]
                point.append(m0 - m1)
            lo, hi = np.percentile(dd, [100 * (1 - ci) / 2, 100 * (1 + ci) / 2]) if len(dd) > 10 else (np.nan, np.nan)
            row = dict(model_a=a, model_b=b, metric=metric, mean_difference_a_minus_b=float(np.nanmean(point)),
                       ci_low=float(lo), ci_high=float(hi),
                       ci_excludes_zero=bool(np.isfinite(lo) and (lo > 0 or hi < 0)))
            if metric == "balanced_accuracy":
                ca, cb = (pa == ya[None]), (pb == ya[None])
                n_a, n_b = (ca & ~cb).sum(1), (~ca & cb).sum(1)
                pv = [spstats.binomtest(int(x), int(x + y_), 0.5).pvalue if (x + y_) > 0 else 1.0 for x, y_ in zip(n_a, n_b)]
                row.update(mcnemar_a_only_correct=int(n_a.sum()), mcnemar_b_only_correct=int(n_b.sum()),
                           mcnemar_exact_p_per_seed=";".join("%.3f" % p for p in pv))
            rows.append(row)
    return pd.DataFrame(rows)


def assign_activity_tables(ctx: Ctx, rec_pooled: pd.DataFrame, win_pooled: pd.DataFrame) -> pd.DataFrame:
    """Activity-wise and activity-group metrics (recording + window level) from pooled test predictions."""
    rows = []
    meta = ctx.rec_df.set_index("rec_idx")[["activity", "activity_group"]]
    rp = rec_pooled.join(meta, on="rec_idx")
    wp = win_pooled.join(meta, on="rec_idx")
    spec_groups = ctx.cfg.activity.groups
    units = [("activity", a, [a]) for a in sorted(rp.activity.unique())]
    units += [("group", g, acts) for g, acts in spec_groups.items()]
    units.append(("paired_activities_all", "all eligible activities", list(ctx.eligible)))
    for level, df_, fn in (("recording", rp, lambda d, keys: recording_metrics_table(d, keys)),
                           ("window", wp, lambda d, keys: window_metrics_table(d, keys))):
        for utype, name, acts in units:
            sub = df_[df_.activity.isin(acts)]
            if sub.empty:
                continue
            t = fn(sub, ["seed", "model"])
            t["unit_type"], t["unit"], t["level"] = utype, name, level
            t["n_recordings"] = sub.rec_idx.nunique()
            rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    g = out.groupby(["model", "level", "unit_type", "unit"], sort=False)
    agg = g[METRIC_COLS].mean().add_suffix("_mean").join(g[METRIC_COLS].std(ddof=1).add_suffix("_std"))
    agg["n_seeds"] = g.seed.nunique()
    agg["n_recordings"] = g.n_recordings.first()
    agg["n_healthy_units"] = g.n_neg.first()
    agg["n_epilepsy_units"] = g.n_pos.first()
    return agg.reset_index()


def noise_tables(ctx: Ctx, noise_frames: pd.DataFrame) -> pd.DataFrame:
    """Per model x condition performance (pooled over folds, averaged over seeds) with degradation vs clean."""
    keys = ["seed", "model", "condition", "noise_type", "snr_db"]     # caller passes snr_db=1e9 / 'clean' for clean rows
    rec = recording_frame(noise_frames, keys)
    rm = recording_metrics_table(rec, keys)
    wm = window_metrics_table(noise_frames, keys)
    rm["level"], wm["level"] = "recording", "window"
    allm = pd.concat([rm, wm], ignore_index=True)
    g = allm.groupby(["model", "level", "condition", "noise_type", "snr_db"], sort=False)
    agg = g[METRIC_COLS].mean().add_suffix("_mean").join(g[METRIC_COLS].std(ddof=1).add_suffix("_std"))
    agg["n_seeds"] = g.seed.nunique()
    agg = agg.reset_index()
    clean = agg[agg.condition == "clean"].set_index(["model", "level"])
    for m in ("accuracy", "balanced_accuracy", "macro_f1"):
        agg["delta_%s_vs_clean" % m] = agg.apply(
            lambda r: r[m + "_mean"] - clean.loc[(r.model, r.level), m + "_mean"] if (r.model, r.level) in clean.index else np.nan, axis=1)
    agg["snr_db"] = agg.snr_db.where(agg.snr_db < 1e8, np.nan)
    return agg


# =============================================================================
# SELF-TESTS (executed at start; the run aborts if a core component is wrong)
# =============================================================================
def run_self_tests(cfg: Cfg, device) -> dict:
    res, fs = {}, cfg.data.fs
    # 1. GWST vs direct evaluation of Eq. (1)-(3) (integer k)
    N, ks = 64, [3, 7, 12]
    z = np.random.default_rng(0).standard_normal(N)
    g = GWST(N, fs, np.array(ks) * fs / N)
    err = float(np.max(np.abs(g.transform(z) - naive_stockwell_integer_k(z, ks))))
    res["gwst_vs_direct_definition_max_abs_error"] = err
    assert err < 1e-9, "GWST disagrees with direct Stockwell definition (%g)" % err
    # 2. GWST localises a 10 Hz sinusoid
    Ns = int(round(cfg.window.seconds * fs))
    fr = np.linspace(cfg.gwst.fmin, cfg.gwst.fmax, int(cfg.gwst.n_freq))
    gg = GWST(Ns, fs, fr)
    s = np.sin(2 * np.pi * 10.0 * np.arange(Ns) / fs)
    peak_f = float(fr[np.argmax(np.abs(gg.transform(s)).mean(axis=1))])
    res["gwst_peak_frequency_of_10Hz_sine"] = peak_f
    assert abs(peak_f - 10.0) < 0.5, "GWST frequency localisation failed"
    # 3. WOSG removes slow drift and preserves 10 Hz content
    t = np.arange(10240) / fs
    clean = np.sin(2 * np.pi * 10 * t)
    drift = 8 * np.sin(2 * np.pi * 0.15 * t) + 3 * t / t[-1]
    y, info = wosg_filter(clean + drift, fs, cfg.wosg)
    lp_before, lp_after = _lowpower(clean + drift, fs, 0.5), _lowpower(y, fs, 0.5)
    amp = float(np.std(_fft_band(y, fs, 8, 12)) / np.std(clean))
    res["wosg_lowfreq_power_reduction_factor"] = lp_before / max(lp_after, 1e-18)
    res["wosg_10Hz_amplitude_ratio"] = amp
    assert lp_after < 0.1 * lp_before and 0.9 < amp < 1.1, "WOSG self-test failed"
    # 4. entropy helper
    ent_u = float(row_entropy(np.linspace(0, 1, 10000)[None, :], 10)[0])
    ent_c = float(row_entropy(np.ones((1, 100)), 10)[0])
    res["entropy_uniform_bits"], res["entropy_constant_bits"] = ent_u, ent_c
    assert abs(ent_u - math.log2(10)) < 0.01 and ent_c == 0.0
    # 5. segmentation of 10,241 samples
    W, st, left = segment_signal(np.arange(10241.0), 2560, 2560)
    res["segmentation_10241_samples"] = {"windows": int(len(W)), "leftover": int(left)}
    assert W.shape == (4, 2560) and left == 1
    # 6. metrics unavailable for single-class sets (never invented)
    m = compute_metrics([1, 1, 1], [0.9, 0.8, 0.2], [1, 1, 0])
    assert np.isnan(m["roc_auc"]) and np.isnan(m["balanced_accuracy"]) and np.isnan(m["specificity"])
    # 7. grouped splitting never crosses recordings
    rng = np.random.default_rng(1)
    rec = np.repeat(np.arange(40), 4)
    lab = (np.arange(40) % 3 == 0).astype(int)
    wdf = pd.DataFrame({"rec_idx": rec, "label": lab[rec]})
    for tr, te in outer_folds(wdf, np.ones(len(wdf), bool), 5, 0):
        assert not (set(rec[tr]) & set(rec[te]))
    # 8. noise determinism
    nc = dict(cfg.noise)
    x0 = np.random.default_rng(2).standard_normal(5120)
    for kind in cfg.noise.types:
        a = corrupt_signal(x0, 1.0, kind, 10, "rec", fs, nc)
        b = corrupt_signal(x0, 1.0, kind, 10, "rec", fs, nc)
        assert np.array_equal(a, b)
        got = 10 * np.log10(np.var(x0) / np.var(a - x0))
        assert abs(got - 10 + 10 * np.log10(np.var(x0))) < 0.2 or abs(10 * np.log10(1.0 / np.var(a - x0)) - 10) < 0.2
    # 9. token shape
    sc = TokenScaler(cfg.tokens.n_tokens, cfg.tokens.pool)
    sc.a0 = 1.0
    tok = sc.raw_tokens(np.abs(rng.standard_normal((2, 225, Ns))).astype(np.float32))
    res["token_shape"] = list(tok.shape)
    assert tok.shape == (2, cfg.tokens.n_tokens, 225)
    # 10. encoder shapes
    for kind in ("transformer", "bilstm"):
        e = EEGEncoder(kind, 225, cfg)
        o = e(torch.randn(3, cfg.tokens.n_tokens, 225))
        assert tuple(o.shape) == (3, cfg.tokens.embed_dim) and float(o.abs().max()) <= 1.0
        assert tuple(e.encode32(torch.randn(3, cfg.tokens.n_tokens, 225)).shape) == (3, cfg.tokens.token_dim)
    res["all_passed"] = True
    return res


# =============================================================================
# MODEL PARAMETER COUNTS / CIRCUIT CONFIG
# =============================================================================
def model_inventory(cfg: Cfg, n_freq: int) -> dict:
    inv = {"n_freq_F": n_freq}
    for kind in ("transformer", "bilstm"):
        e = EEGEncoder(kind, n_freq, cfg)
        inv[kind] = {"total_trainable_encoder_incl_projection_and_embedding": n_params(e),
                     "token_projection": n_params(e.proj), "core_incl_attention_pooling": n_params(e.core),
                     "embedding_layer": n_params(e.embed)}
    inv["heads"] = {"linear(6,1)": n_params(LinearHead()), "mlp(6-6-1)": n_params(MLPHead(6, cfg.model.mlp_hidden))}
    if HAVE_PENNYLANE:
        for nm, ent in (("vqc_6q_2layers_ring", True), ("vqc_no_cnot", False)):
            h = QuantumHead(cfg.quantum, ent)
            inv["heads"][nm] = {"total": n_params(h), "circuit_weights": int(h.weights.numel()),
                                "output_linear(6,1)": n_params(h.out)}
        inv["quantum_circuit"] = {"n_qubits": cfg.quantum.n_qubits, "layers": cfg.quantum.n_layers,
                                  "encoding": "RY(pi*z_i)", "variational": "RY(theta) RZ(phi) per qubit per layer",
                                  "entanglement": "CNOT ring 0->1->2->3->4->5->0 after the rotations of each layer",
                                  "measurement": "<Z_i> for i=0..5 -> Linear(6,1)", "simulator": cfg.quantum.device,
                                  "diff_method": cfg.quantum.diff_method}
    return inv


# =============================================================================
# PLOTS
# =============================================================================
SHORT = {"E1": "RF-450", "E2": "SVM-450", "E3": "MI+RF", "E4": "T+Linear", "E5": "T+MLP", "E6": "T+RBF-SVM",
         "E7": "T+VQC", "E8": "B+Linear", "E9": "B+MLP", "E10": "B+RBF-SVM", "E11": "B+VQC",
         "E12T": "T+VQC(noCNOT)", "E12B": "B+VQC(noCNOT)", "FT-T-lin": "FT T+Linear", "FT-T-mlp": "FT T+MLP",
         "FT-T-vqc": "FT T+VQC", "FT-B-lin": "FT B+Linear", "FT-B-mlp": "FT B+MLP", "FT-B-vqc": "FT B+VQC"}


def model_color(eid: str) -> str:
    e = EXPERIMENTS[eid]
    return PALETTE[0] if e["enc"] is None else (PALETTE[1] if e["enc"] == "transformer" else PALETTE[2])


def _style():
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 100, "savefig.bbox": "tight"})


def _save(fig, path: Path, dpi=200):
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def pick_example(ctx: Ctx, label: int, prefer=("running", "walking", "jogging", "sitting")) -> str:
    sub = ctx.rec_df[ctx.rec_df.label == label]
    for a in prefer:
        s = sub[sub.activity == a]
        if len(s):
            return s.rec_id.iloc[0]
    return sub.rec_id.iloc[0]


def plot_signals(ctx: Ctx) -> None:
    _style()
    fs = ctx.cfg.data.fs
    for lab, fname, title in ((0, "healthy_eeg_example.png", "Healthy"), (1, "epilepsy_eeg_example.png", "Epilepsy")):
        rid = pick_example(ctx, lab, ("walking", "running"))
        r = ctx.rec_df[ctx.rec_df.rec_id == rid].iloc[0]
        fig, ax = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
        t = np.arange(len(ctx.raw_used[rid])) / fs
        ax[0].plot(t, ctx.raw_used[rid] - np.mean(ctx.raw_used[rid]), lw=0.6, color=PALETTE[7])
        ax[0].set_title("%s FP1 EEG - %s (%s) - raw (mean removed)" % (title, rid, r.activity))
        ax[1].plot(t[:len(ctx.filt[rid])], ctx.filt[rid], lw=0.6, color=PALETTE[0])
        ax[1].set_title("after WOSG (window=%s, polyorder=%s)" % (ctx.wosg_info[rid].get("window"), ctx.wosg_info[rid].get("polyorder")))
        ax[1].set_xlabel("time (s)")
        for a_ in ax:
            a_.set_ylabel("amplitude (a.u.)")
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / fname)
    fig, axs = plt.subplots(2, 2, figsize=(12, 6))
    for j, (lab, nm) in enumerate(((0, "Healthy"), (1, "Epilepsy"))):
        rid = pick_example(ctx, lab, ("running", "jogging", "walking"))
        r = ctx.rec_df[ctx.rec_df.rec_id == rid].iloc[0]
        n = int(10 * fs)
        t = np.arange(n) / fs
        axs[0, j].plot(t, (ctx.raw_used[rid] - np.mean(ctx.raw_used[rid]))[:n], lw=0.6, color=PALETTE[7])
        axs[0, j].set_title("%s - %s: raw" % (nm, r.activity))
        axs[1, j].plot(t, ctx.filt[rid][:n], lw=0.6, color=PALETTE[0])
        axs[1, j].plot(t, (ctx.raw_used[rid] - np.mean(ctx.raw_used[rid]))[:n], lw=0.4, color=PALETTE[7], alpha=0.35,
                       label="raw (mean removed)")
        axs[1, j].set_title("%s - %s: WOSG-filtered (blue) vs raw (grey)" % (nm, r.activity))
        axs[1, j].set_xlabel("time (s)")
        axs[1, j].legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "raw_vs_filtered.png")
    save_json({"wosg": dict(ctx.cfg.wosg), "chosen_parameters_example_recordings": {
        k: ctx.wosg_info[k] for k in list(ctx.wosg_info)[:3]}}, ctx.dirs["config"] / "wosg_example_info.json")


def plot_gwst(ctx: Ctx) -> None:
    _style()
    cfg = ctx.cfg
    for lab, fname, nm in ((0, "gwst_healthy.png", "Healthy"), (1, "gwst_epilepsy.png", "Epilepsy")):
        rid = pick_example(ctx, lab, ("running", "jogging", "walking"))
        wi = int(ctx.win_df[(ctx.win_df.rec_id == rid) & (ctx.win_df.win_idx == 0)].index[0])
        S = np.asarray(ctx.Smag[wi])
        fig, ax = plt.subplots(2, 1, figsize=(9, 6.5), gridspec_kw={"height_ratios": [1, 2.4]}, sharex=True)
        t = np.arange(S.shape[1]) / cfg.data.fs
        ax[0].plot(t, ctx.windows_raw[wi], lw=0.6, color=PALETTE[0])
        ax[0].set_title("%s - %s (%s), first 5 s window after WOSG" % (nm, rid, ctx.rec_df[ctx.rec_df.rec_id == rid].activity.iloc[0]))
        ax[0].set_ylabel("amplitude")
        im = ax[1].imshow(S, aspect="auto", origin="lower", extent=[0, t[-1], cfg.gwst.fmin, cfg.gwst.fmax],
                          cmap="viridis", vmax=np.percentile(S, 99.5))
        ax[1].set_ylabel("frequency (Hz)")
        ax[1].set_xlabel("time (s)")
        ax[1].set_title("|GWST| (%d frequency bins, 0.5-50 Hz)" % S.shape[0])
        ax[1].grid(False)
        fig.colorbar(im, ax=ax, label="|GWST|", fraction=0.025)
        _save(fig, ctx.dirs["plots"] / fname)


def plot_training_curves(ctx: Ctx) -> None:
    _style()
    for kind, fname in (("transformer", "training_loss_transformer.png"), ("bilstm", "training_loss_bilstm.png")):
        hs = [h for h in ctx.histories if h["kind"] == kind]
        if not hs:
            continue
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        for h in hs:
            ax[0].plot(h["train_loss"], color=PALETTE[0], alpha=0.25, lw=0.8)
            ax[0].plot(h["val_loss"], color=PALETTE[1], alpha=0.25, lw=0.8)
            ax[1].plot(h["val_bal_acc"], color=PALETTE[2], alpha=0.35, lw=0.8)
        L = max(len(h["train_loss"]) for h in hs)
        def mean_curve(key):
            M = np.full((len(hs), L), np.nan)
            for i, h in enumerate(hs):
                M[i, :len(h[key])] = h[key]
            return np.nanmean(M, axis=0)
        ax[0].plot(mean_curve("train_loss"), color=PALETTE[0], lw=2, label="train (mean)")
        ax[0].plot(mean_curve("val_loss"), color=PALETTE[1], lw=2, label="validation (mean)")
        ax[1].plot(mean_curve("val_bal_acc"), color=PALETTE[2], lw=2, label="val balanced acc. (mean)")
        ax[0].set_title("%s pre-training loss (%d runs = seeds x folds)" % (kind, len(hs)))
        ax[0].set_xlabel("epoch"); ax[0].set_ylabel("weighted BCE-with-logits"); ax[0].legend()
        ax[1].set_title("validation window-level balanced accuracy @0.5"); ax[1].set_xlabel("epoch"); ax[1].legend()
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / fname)


def _bar_color_hatch(eid):
    return model_color(eid), ("//" if EXPERIMENTS[eid].get("head") in QUANTUM_HEADS else "")


def plot_confusions(ctx: Ctx, rec_fold: pd.DataFrame, win_clean: pd.DataFrame) -> None:
    _style()
    models = [m for m in EXPERIMENTS if EXPERIMENTS[m]["family"] != "finetune" and m in set(rec_fold.model)]
    seed0 = sorted(rec_fold.seed.unique())[0]
    for level, fname, df in (("recording", "confusion_matrix.png", rec_fold[rec_fold.seed == seed0]),
                             ("window", "confusion_matrix_window.png", win_clean[win_clean.seed == seed0])):
        n = len(models)
        cols = min(5, n)
        rows = int(math.ceil(n / cols))
        fig, axs = plt.subplots(rows, cols, figsize=(3.0 * cols, 3.0 * rows))
        axs = np.atleast_1d(axs).ravel()
        for ax, m in zip(axs, models):
            d = df[df.model == m]
            if level == "recording":
                y, p = d.label.values, d.pred.values
            else:
                y, p = d.label.values, (d.prob.values >= d.thr_w.values).astype(int)
            cm = np.array([[np.sum((y == 0) & (p == 0)), np.sum((y == 0) & (p == 1))],
                           [np.sum((y == 1) & (p == 0)), np.sum((y == 1) & (p == 1))]])
            ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(cm.max(), 1))
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                            color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=11)
            ax.set_xticks([0, 1]); ax.set_xticklabels(["Healthy", "Epilepsy"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["Healthy", "Epilepsy"])
            ax.set_title("%s %s" % (m, SHORT[m]), fontsize=8); ax.grid(False)
            ax.set_xlabel("predicted"); ax.set_ylabel("true")
        for ax in axs[len(models):]:
            ax.axis("off")
        fig.suptitle("%s-level confusion matrices, pooled over outer test folds (seed %d, validation-selected thresholds)" % (level.capitalize(), seed0), y=1.01)
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / fname)


def plot_roc(ctx: Ctx, rec_fold: pd.DataFrame) -> None:
    _style()
    from sklearn.metrics import roc_curve
    seed0 = sorted(rec_fold.seed.unique())[0]
    d0 = rec_fold[rec_fold.seed == seed0]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
    groups = [("Transformer branch", ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E12T"]),
              ("Bi-LSTM branch", ["E1", "E2", "E3", "E8", "E9", "E10", "E11", "E12B"])]
    for ax, (title, ms) in zip(axs, groups):
        for k, m in enumerate([x for x in ms if x in set(d0.model)]):
            d = d0[d0.model == m]
            if d.label.nunique() < 2:
                continue
            fpr, tpr, _ = roc_curve(d.label, d.mean_prob)
            auc = roc_auc_score(d.label, d.mean_prob)
            ax.plot(fpr, tpr, lw=1.6, color=PALETTE[k % 8], ls="-" if "VQC" not in SHORT[m] else "--", label="%s (AUC %.2f)" % (SHORT[m], auc))
        ax.plot([0, 1], [0, 1], color="grey", lw=0.8, ls=":")
        ax.set_title("%s - recording-level ROC (pooled, seed %d)" % (title, seed0))
        ax.set_xlabel("1 - specificity"); ax.set_ylabel("sensitivity"); ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "roc_curves.png")


def plot_activity(ctx: Ctx, act: pd.DataFrame) -> None:
    _style()
    if act is None or act.empty:
        return
    show = [m for m in ["E1", "E2", "E5", "E7", "E9", "E11"] if m in set(act.model)]
    sub = act[(act.level == "recording") & act.model.isin(show)]
    units = [u for u in ctx.eligible] + list(ctx.cfg.activity.groups) + ["all eligible activities"]
    fig, axs = plt.subplots(2, 1, figsize=(13, 8))
    for ax, metric, title in zip(axs, ("accuracy_mean", "balanced_accuracy_mean"), ("Recording-level accuracy", "Recording-level balanced accuracy")):
        w = 0.8 / max(len(show), 1)
        for k, m in enumerate(show):
            vals = []
            for u in units:
                v = sub[(sub.model == m) & (sub.unit == u)][metric]
                vals.append(float(v.iloc[0]) if len(v) else np.nan)
            c, h = _bar_color_hatch(m)
            ax.bar(np.arange(len(units)) + k * w - 0.4 + w / 2, vals, w, color=c, hatch=h, edgecolor="white", alpha=0.55 + 0.4 * (k % 2), label="%s %s" % (m, SHORT[m]))
        ax.set_xticks(np.arange(len(units))); ax.set_xticklabels(units, rotation=25, ha="right")
        ax.set_ylim(0, 1.05); ax.set_title(title + " per activity / activity group (pooled outer-CV test predictions)")
        ax.axhline(0.5, color="grey", lw=0.7, ls=":")
    axs[0].legend(ncol=3, fontsize=7)
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "activity_comparison.png")


def plot_holdout(ctx: Ctx, hs: pd.DataFrame) -> None:
    _style()
    if hs is None or hs.empty:
        return
    sub = hs[hs.level == "recording"]
    models = [m for m in EXPERIMENTS if m in set(sub.model)]
    acts = sorted(sub.heldout.unique())
    fig, axs = plt.subplots(2, 1, figsize=(13, 8))
    for ax, metric, title in zip(axs, ("accuracy_mean", "balanced_accuracy_mean"), ("accuracy", "balanced accuracy")):
        w = 0.85 / max(len(models), 1)
        for k, m in enumerate(models):
            vals = [float(sub[(sub.model == m) & (sub.heldout == a)][metric].iloc[0]) if len(sub[(sub.model == m) & (sub.heldout == a)]) else np.nan for a in acts]
            c, h = _bar_color_hatch(m)
            ax.bar(np.arange(len(acts)) + k * w - 0.425 + w / 2, vals, w, color=c, hatch=h, edgecolor="white", alpha=0.5 + 0.4 * (k % 2), label="%s %s" % (m, SHORT[m]))
        ax.set_xticks(np.arange(len(acts))); ax.set_xticklabels(acts)
        ax.set_ylim(0, 1.05); ax.axhline(0.5, color="grey", lw=0.7, ls=":")
        ax.set_title("Leave-one-activity-out, recording-level %s (held-out activity on x-axis)" % title)
    axs[0].legend(ncol=4, fontsize=6.5)
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "activity_holdout_comparison.png")


def plot_noise(ctx: Ctx, nt: pd.DataFrame) -> None:
    _style()
    if nt is None or nt.empty:
        return
    sub = nt[nt.level == "recording"]
    models = [m for m in ["E1", "E2", "E5", "E7", "E9", "E11", "E12T", "E12B"] if m in set(sub.model)]
    types = [t for t in ctx.cfg.noise.types if t in set(sub.noise_type)]
    snrs = sorted(ctx.cfg.noise.snr_db)                      # ascending (5, 10, 20), then clean
    xlab = ["%g dB" % s for s in snrs] + ["clean"]
    for metric, fname, yl in (("accuracy_mean", "noise_robustness.png", "recording-level accuracy"),
                              ("balanced_accuracy_mean", "noise_robustness_balanced_accuracy.png", "recording-level balanced accuracy")):
        fig, axs = plt.subplots(1, len(types), figsize=(4.2 * len(types), 4.2), sharey=True)
        axs = np.atleast_1d(axs)
        for ax, t in zip(axs, types):
            for k, m in enumerate(models):
                ys = []
                for s in snrs:
                    v = sub[(sub.model == m) & (sub.noise_type == t) & (np.isclose(sub.snr_db, s))][metric]
                    ys.append(float(v.iloc[0]) if len(v) else np.nan)
                cl = sub[(sub.model == m) & (sub.noise_type == "clean")][metric]
                ys.append(float(cl.iloc[0]) if len(cl) else np.nan)
                ax.plot(range(len(xlab)), ys, marker="o", ms=4, lw=1.4, color=PALETTE[k % 8],
                        ls="--" if "VQC" in SHORT[m] else "-", label="%s %s" % (m, SHORT[m]))
            ax.set_xticks(range(len(xlab))); ax.set_xticklabels(xlab)
            ax.set_title(NOISE_LABELS.get(t, t)); ax.set_xlabel("signal-to-noise ratio"); ax.set_ylim(0, 1.02)
        axs[0].set_ylabel(yl)
        axs[-1].legend(fontsize=6.5, loc="lower right")
        fig.suptitle("Synthetic-corruption robustness of already-trained models (clean-trained, no re-tuning)", y=1.02)
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / fname)
    noisy = sub[(sub.noise_type != "clean")]
    if len(noisy):
        d = noisy.groupby("model")["delta_balanced_accuracy_vs_clean"].mean().reindex([m for m in EXPERIMENTS if m in set(noisy.model)]).dropna()
        fig, ax = plt.subplots(figsize=(9, 4))
        cols = [model_color(m) for m in d.index]
        ax.bar(range(len(d)), d.values, color=cols, hatch=["//" if EXPERIMENTS[m].get("head") in QUANTUM_HEADS else "" for m in d.index], edgecolor="white")
        ax.set_xticks(range(len(d))); ax.set_xticklabels([SHORT[m] for m in d.index], rotation=35, ha="right")
        ax.set_ylabel("mean change in balanced accuracy vs clean"); ax.axhline(0, color="k", lw=0.7)
        ax.set_title("Model-wise robustness (mean over all synthetic corruption types and SNRs)")
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / "noise_model_comparison.png")


def plot_noise_examples(ctx: Ctx) -> None:
    _style()
    cfg = ctx.cfg
    rid = pick_example(ctx, 0, ("walking", "sitting"))
    ridx = int(ctx.rec_df[ctx.rec_df.rec_id == rid].rec_idx.iloc[0])
    x = ctx.raw_used[rid]
    fs = cfg.data.fs
    n = int(5 * fs)
    t = np.arange(n) / fs
    kinds = list(cfg.noise.types)
    snr_show = float(cfg.noise.snr_db[len(cfg.noise.snr_db) // 2])
    fig, axs = plt.subplots(len(kinds) + 1, 1, figsize=(10, 2.0 * (len(kinds) + 1)), sharex=True)
    axs[0].plot(t, x[:n] - x.mean(), color=PALETTE[7], lw=0.6)
    axs[0].set_title("Clean raw recording %s (first 5 s, mean removed)" % rid)
    ref = float(np.var(ctx.filt[rid] if cfg.noise.snr_reference == "filtered" else x))
    params = {"snr_reference": cfg.noise.snr_reference, "SNR_dB_values": list(cfg.noise.snr_db), "noise_seed": cfg.noise.seed,
              "definitions": {"SNR": "10*log10(P_reference / P_noise); P_reference = variance of the %s recording" % cfg.noise.snr_reference,
                              "gaussian": "white Gaussian noise",
                              "baseline_drift": "sum of 4 sinusoids %s Hz + slow ramp" % cfg.noise.drift_freq_hz,
                              "emg_like": "band-pass %s Hz noise with bursty envelope (SYNTHETIC, not real EMG)" % cfg.noise.emg_band_hz,
                              "ocular_like": "Poisson blink-like Gaussian pulses (width ~%.2f s, rate %.2f/s) + %s Hz eye-movement-like noise (SYNTHETIC)" % (
                                  cfg.noise.blink_width_s, cfg.noise.blink_rate_per_s, cfg.noise.ocular_band_hz)},
              "example_recording": rid, "example_reference_power": ref}
    for ax, k in zip(axs[1:], kinds):
        xc = corrupt_signal(x, ref, k, snr_show, rid, fs, dict(cfg.noise))
        ax.plot(t, x[:n] - x.mean(), color=PALETTE[7], lw=0.5, alpha=0.5, label="clean")
        ax.plot(t, xc[:n] - xc.mean(), color=PALETTE[1], lw=0.6, label="corrupted")
        ax.set_title("%s @ %g dB SNR" % (NOISE_LABELS.get(k, k), snr_show), fontsize=9)
    axs[-1].set_xlabel("time (s)"); axs[1].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "noise_examples.png")
    save_json(params, ctx.dirs["config"] / "noise_parameters.json")


def plot_recording_level(ctx: Ctx, rec_fold: pd.DataFrame) -> None:
    _style()
    seed0 = sorted(rec_fold.seed.unique())[0]
    d0 = rec_fold[rec_fold.seed == seed0]
    models = [m for m in ["E5", "E7", "E9", "E11"] if m in set(d0.model)]
    if not models:
        return
    meta = ctx.rec_df.set_index("rec_idx")
    order = meta.sort_values(["label", "activity_group", "activity"]).index.tolist()
    fig, axs = plt.subplots(len(models), 1, figsize=(13, 2.8 * len(models)), sharex=True)
    axs = np.atleast_1d(axs)
    for ax, m in zip(axs, models):
        d = d0[d0.model == m].set_index("rec_idx")
        xs = [i for i, r in enumerate(order) if r in d.index]
        ys = [d.loc[order[i], "mean_prob"] for i in xs]
        lab = [int(d.loc[order[i], "label"]) for i in xs]
        ax.scatter(xs, ys, c=[PALETTE[1] if l else PALETTE[0] for l in lab], s=22, edgecolor="k", linewidth=0.3)
        ax.axhline(float(d.thr_r.median()), color="k", ls="--", lw=0.8, label="median validation threshold")
        ax.set_ylim(-0.02, 1.02); ax.set_ylabel("mean window prob.")
        ax.set_title("%s %s - recording-level mean probability (blue=healthy, orange=epilepsy; seed %d)" % (m, SHORT[m], seed0), fontsize=9)
    axs[0].legend(fontsize=7)
    axs[-1].set_xlabel("recordings sorted by class, activity group, activity")
    fig.tight_layout()
    _save(fig, ctx.dirs["plots"] / "recording_level_results.png")


def plot_model_comparison(ctx: Ctx, rec_sum: pd.DataFrame) -> None:
    _style()
    for fam_ft, fname, ttl in ((False, "model_comparison.png", "Frozen-encoder / classical baselines"),
                               (True, "model_comparison_finetuned.png", "End-to-end FINE-TUNED models (separate comparison)")):
        d = rec_sum[rec_sum.model.map(lambda m: (EXPERIMENTS[m]["family"] == "finetune") == fam_ft)]
        if d.empty:
            continue
        d = d.sort_values("model", key=lambda s: s.map(lambda m: list(EXPERIMENTS).index(m)))
        fig, ax = plt.subplots(figsize=(9, 0.42 * len(d) + 1.8))
        y = np.arange(len(d))[::-1]
        for yy, (_, r) in zip(y, d.iterrows()):
            c, h = _bar_color_hatch(r.model)
            ax.barh(yy, r.balanced_accuracy, color=c, hatch=h, edgecolor="white", alpha=0.85)
            if np.isfinite(r.get("balanced_accuracy_ci_low", np.nan)):
                ax.plot([r.balanced_accuracy_ci_low, r.balanced_accuracy_ci_high], [yy, yy], color="k", lw=1.2)
            ax.text(0.01, yy, " %.3f" % r.balanced_accuracy, va="center", color="white", fontsize=7)
        ax.set_yticks(y); ax.set_yticklabels(["%s %s" % (m, SHORT[m]) for m in d.model])
        ax.set_xlim(0, 1); ax.axvline(0.5, color="grey", ls=":", lw=0.8)
        ax.set_xlabel("recording-level balanced accuracy (pooled outer-CV test; whiskers = 95% bootstrap CI over recordings)")
        ax.set_title(ttl + " - blue: handcrafted-450, orange: Transformer, green: Bi-LSTM, hatched: VQC")
        fig.tight_layout()
        _save(fig, ctx.dirs["plots"] / fname)


# =============================================================================
# DIAGRAMS
# =============================================================================
def _gv_render(g, stem: Path) -> bool:
    if not (HAVE_GRAPHVIZ_PY and HAVE_DOT):
        return False
    ok = True
    for fmt in ("png", "svg"):
        try:
            g.render(filename=stem.name, directory=str(stem.parent), format=fmt, cleanup=True)
        except Exception as e:  # pragma: no cover
            LOG.warning("Graphviz render %s failed: %s", fmt, e)
            ok = False
    return ok


def _mpl_flow(steps: list[tuple[str, str]], stem: Path, title: str, ncols=1) -> None:
    """Matplotlib fallback: vertical flow of boxes (used only when Graphviz is unavailable)."""
    n = len(steps)
    fig, ax = plt.subplots(figsize=(7, 0.9 * n + 1))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, n + 0.5)
    for i, (txt, _) in enumerate(steps):
        y = n - i - 0.5
        ax.add_patch(FancyBboxPatch((1.5, y - 0.35), 7, 0.7, boxstyle="round,pad=0.02", fc="#EAF2F8", ec="#34495E"))
        ax.text(5, y, txt, ha="center", va="center", fontsize=8)
        if i < n - 1:
            ax.annotate("", xy=(5, y - 0.45), xytext=(5, y - 0.35 + 0.0), arrowprops=dict(arrowstyle="->"))
    ax.set_title(title)
    for fmt in ("png", "svg"):
        fig.savefig(str(stem) + "." + fmt, dpi=200, bbox_inches="tight")
    plt.close(fig)


def diagram_architecture(ctx: Ctx) -> None:
    cfg = ctx.cfg
    stem = ctx.dirs["diagrams"] / "complete_architecture"
    F_ = ctx.n_freq if hasattr(ctx, "n_freq") else cfg.gwst.n_freq
    if not (HAVE_GRAPHVIZ_PY and HAVE_DOT):
        _mpl_flow([("Wearable EEG FP1 (512 Hz)", ""), ("Dataset audit + recording-level split", ""), ("WOSG filtering", ""),
                   ("5 s segmentation", ""), ("GWST (0.5-50 Hz)", ""), ("log|GWST|, 64 tokens", ""),
                   ("Linear F->32", ""), ("Transformer OR Bi-LSTM", ""), ("Attention pooling", ""),
                   ("6-D embedding", ""), ("6-qubit VQC (RY enc., 2 layers, CNOT ring, <Z>)", ""),
                   ("Linear(6,1)", ""), ("Healthy/Epilepsy probability", ""), ("Recording-level aggregation", "")], stem,
                  "Complete architecture (Graphviz unavailable: Matplotlib fallback)")
        return
    g = _graphviz.Digraph("arch", graph_attr=dict(rankdir="TB", fontname="Helvetica", nodesep="0.35", ranksep="0.38", dpi="200", labelloc="t",
                                                  label="Hybrid quantum-classical EEG epilepsy detection - complete proposed architecture"),
                          node_attr=dict(shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11", fillcolor="#EAF2F8", color="#34495E"),
                          edge_attr=dict(color="#34495E", arrowsize="0.8"))
    def N(i, t, **k): g.node(i, t, **k)
    N("eeg", "Wearable EEG (FP1, NeuroSky MindWave 2.0)\n512 Hz, raw single channel", fillcolor="#FDEBD0")
    N("aud", "Dataset audit + recording-level grouped split\n(StratifiedGroupKFold; no window leakage)")
    N("wosg", "WOSG filtering\nDWT -> optimised Savitzky-Golay on approximation -> subtract")
    N("seg", "Five-second segmentation\n2,560 samples / window")
    N("gwst", "Gaussian-window Stockwell transform (GWST)\n0.5-50 Hz, %d frequency bins" % F_)
    g.node("l1", "L1-norm\n(%d)" % F_, fillcolor="#D5F5E3"); g.node("ent", "Shannon entropy\n10-bin histogram (%d)" % F_, fillcolor="#D5F5E3")
    N("cat", "Concatenate -> %d-D features\n(train-only MI selection in E3)" % (2 * F_), fillcolor="#D5F5E3")
    N("rf", "Random Forest (E1, E3)\nSVM (E2)", fillcolor="#D5F5E3")
    N("tok", "log(1 + |GWST| / a0)  (a0 from training data)\nmean-pool 40 samples -> 64 tokens x F=%d\nper-frequency standardisation (train stats)" % F_)
    N("proj", "Linear projection F -> 32\ninput [B, 64, 32]")
    N("tr", "Transformer encoder\n2 pre-norm blocks, 4 heads, FF 64, GELU, dropout 0.1", fillcolor="#FAD7A0")
    N("bl", "Bi-LSTM encoder\n1 layer, 16 hidden / direction, dropout 0.1", fillcolor="#ABEBC6")
    N("pool", "Temporal attention pooling\n[B, 32]")
    N("emb", "LayerNorm(32) -> Linear(32, 6) -> Tanh\nshared 6-D embedding z", fillcolor="#FCF3CF")
    N("q1", "Six-qubit angle encoding\nRY(pi * z_i)", fillcolor="#E8DAEF")
    N("q2", "Two variational layers\ntrainable RY, RZ on all qubits", fillcolor="#E8DAEF")
    N("q3", "CNOT ring entanglement\n0->1->2->3->4->5->0", fillcolor="#E8DAEF")
    N("q4", "Pauli-Z expectation values <Z_0..Z_5>", fillcolor="#E8DAEF")
    N("q5", "Classical output layer Linear(6, 1)\n(logit)", fillcolor="#E8DAEF")
    N("c1", "Linear classifier\n(6 -> 1)", fillcolor="#D6EAF8"); N("c2", "MLP\n(6 -> 6 -> 1, Tanh)", fillcolor="#D6EAF8"); N("c3", "RBF-SVM", fillcolor="#D6EAF8")
    N("prob", "Healthy / Epilepsy window probability\n(sigmoid of logit)", fillcolor="#FADBD8")
    N("rec", "Recording-level aggregation\nmean window probability + validation-selected threshold", fillcolor="#FADBD8")
    for a, b in [("eeg", "aud"), ("aud", "wosg"), ("wosg", "seg"), ("seg", "gwst"), ("gwst", "tok"), ("tok", "proj"),
                 ("proj", "tr"), ("proj", "bl"), ("tr", "pool"), ("bl", "pool"), ("pool", "emb"), ("q1", "q2"),
                 ("q2", "q3"), ("q3", "q4"), ("q4", "q5"), ("emb", "c1"), ("emb", "c2"), ("emb", "c3"), ("q5", "prob"),
                 ("c1", "prob"), ("c2", "prob"), ("c3", "prob"), ("prob", "rec"),
                 ("gwst", "l1"), ("gwst", "ent"), ("l1", "cat"), ("ent", "cat"), ("cat", "rf"), ("rf", "prob")]:
        g.edge(a, b)
    g.edge("emb", "q1", label=" quantum head", fontsize="9", fontname="Helvetica")
    g.attr(size="9,16")
    _gv_render(g, stem)


def diagram_methodology(ctx: Ctx) -> None:
    stem = ctx.dirs["diagrams"] / "methodology_flowchart"
    steps = [("Dataset audit\n(90 CSV, length / format / duplicate checks)", "#FDEBD0"),
             ("Grouped splitting\n5-fold StratifiedGroupKFold by recording + recording-level validation", "#FDEBD0"),
             ("Baseline reproduction\nWOSG -> 5 s -> GWST -> L1+entropy (450-D) -> RF / SVM / MI+RF", "#D5F5E3"),
             ("Classical encoder experiments\nTransformer and Bi-LSTM -> 6-D embedding -> linear / MLP / RBF-SVM", "#D6EAF8"),
             ("Quantum experiments\nSame 6-D embeddings -> 6-qubit VQC, VQC without CNOT (+ separate end-to-end fine-tuning)", "#E8DAEF"),
             ("Recording-level evaluation\nmean window probability, validation threshold, recording-level metrics", "#FADBD8"),
             ("Activity robustness\nactivity-wise, activity-group, leave-one-activity-out", "#FCF3CF"),
             ("Noise robustness\nsynthetic Gaussian / drift / EMG-like / ocular-like at 20, 10, 5 dB", "#FCF3CF"),
             ("Final statistical comparison\nbootstrap CIs over recordings, paired differences, exact McNemar", "#FADBD8")]
    if not (HAVE_GRAPHVIZ_PY and HAVE_DOT):
        _mpl_flow([(s, c) for s, c in steps], stem, "Experimental methodology")
        return
    g = _graphviz.Digraph("meth", graph_attr=dict(rankdir="TB", dpi="200", fontname="Helvetica", nodesep="0.4", ranksep="0.4", labelloc="t",
                                                  label="Experimental methodology"),
                          node_attr=dict(shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11", color="#34495E"),
                          edge_attr=dict(color="#34495E"))
    for i, (t, c) in enumerate(steps):
        g.node("m%d" % i, t, fillcolor=c)
    for a, b in [(0, 1), (1, 2), (1, 3), (1, 4), (3, 4), (2, 5), (3, 5), (4, 5), (5, 6), (5, 7), (6, 8), (7, 8), (5, 8)]:
        g.edge("m%d" % a, "m%d" % b)
    _gv_render(g, stem)
    mermaid = ["flowchart TD"]
    for i, (t, _) in enumerate(steps):
        mermaid.append('    m%d["%s"]' % (i, t.replace("\n", "<br/>").replace('"', "'")))
    for a, b in [(0, 1), (1, 2), (1, 3), (1, 4), (3, 4), (2, 5), (3, 5), (4, 5), (5, 6), (5, 7), (6, 8), (7, 8), (5, 8)]:
        mermaid.append("    m%d --> m%d" % (a, b))
    (ctx.dirs["diagrams"] / "methodology_flowchart.mmd").write_text("\n".join(mermaid) + "\n", encoding="utf-8")
    arch = """flowchart TD
    EEG["Wearable EEG FP1 (512 Hz)"] --> AUD["Dataset audit + recording-level split"]
    AUD --> WOSG["WOSG filtering"] --> SEG["5 s segmentation"] --> GWST["GWST 0.5-50 Hz"]
    GWST --> L1["L1-norm"] & ENT["Shannon entropy"]
    L1 & ENT --> CAT["450-D features"] --> RFSVM["Random Forest / SVM / MI+RF"] --> PROB
    GWST --> TOK["log|GWST|/a0 -> 64 tokens x F"] --> PROJ["Linear F->32"]
    PROJ --> TR["Transformer encoder"] & BL["Bi-LSTM encoder"]
    TR & BL --> POOL["Temporal attention pooling"] --> EMB["6-D embedding (LayerNorm-Linear-Tanh)"]
    EMB --> Q1["6-qubit RY angle encoding"] --> Q2["2 variational layers (RY,RZ)"] --> Q3["CNOT ring"] --> Q4["Pauli-Z measurements"] --> Q5["Linear(6,1)"] --> PROB["Healthy / Epilepsy probability"]
    EMB --> C1["Linear"] & C2["MLP 6-6-1"] & C3["RBF-SVM"] --> PROB
    PROB --> REC["Recording-level aggregation"]
"""
    (ctx.dirs["diagrams"] / "complete_architecture.mmd").write_text(arch, encoding="utf-8")


def diagram_pipeline(ctx: Ctx, stages: list[tuple[str, str]]) -> None:
    stem = ctx.dirs["diagrams"] / "experiment_pipeline"
    if not (HAVE_GRAPHVIZ_PY and HAVE_DOT):
        _mpl_flow([(s, "") for s, _ in stages], stem, "Execution pipeline")
        return
    g = _graphviz.Digraph("pipe", graph_attr=dict(rankdir="LR", dpi="200", fontname="Helvetica", labelloc="t", nodesep="0.3", ranksep="0.35",
                                                  label="Script execution pipeline (stages in hybrid_quantum_eeg_epilepsy.py)"),
                          node_attr=dict(shape="box", style="rounded,filled", fillcolor="#EAF2F8", fontname="Helvetica", fontsize="10", color="#34495E"),
                          edge_attr=dict(color="#34495E"))
    for i, (s, fn) in enumerate(stages):
        g.node("s%d" % i, "%s\n[%s]" % (s, fn))
    deps = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (5, 7), (6, 8), (7, 8), (8, 9), (9, 10), (10, 11), (8, 12)]
    for a, b in deps:
        if a < len(stages) and b < len(stages):
            g.edge("s%d" % a, "s%d" % b)
    _gv_render(g, stem)


PIPELINE_STAGES = [("0 Setup, config, logging, environment", "main"), ("1 Self-tests & gradient checks", "run_self_tests / verify_quantum_gradients"),
                   ("2 Dataset audit", "load_dataset"), ("3 WOSG filtering", "wosg_filter"), ("4 Segmentation + GWST + 450-D features", "build_representation"),
                   ("5 Outer CV: grouped folds, fit E1-E12 + fine-tuning, thresholds", "run_outer_cv / fit_bundle"),
                   ("6 Noise robustness (inside each fold)", "evaluate_noise"), ("7 Leave-one-activity-out", "run_loao"),
                   ("8 Aggregation, bootstrap CI, paired tests", "aggregate_results"), ("9 Plots", "plot_*"), ("10 Diagrams", "diagram_*"),
                   ("11 Reports", "write_reports"), ("12 Metrics CSV export", "aggregate_results")]


def diagram_quantum_circuit(ctx: Ctx) -> None:
    n, L = int(ctx.cfg.quantum.n_qubits), int(ctx.cfg.quantum.n_layers)
    ncol = 1 + L * (2 + n) + 1
    fig, ax = plt.subplots(figsize=(1.0 * ncol + 1.5, 0.9 * n + 1.6))
    ax.set_xlim(-1.3, ncol + 0.2); ax.set_ylim(-n + 0.2, 1.3); ax.axis("off")
    for i in range(n):
        ax.plot([-0.6, ncol - 0.2], [-i, -i], color="k", lw=0.9, zorder=1)
        ax.text(-1.0, -i, r"$q_%d$: $|0\rangle$" % i, ha="right", va="center", fontsize=10)
    def box(x, i, txt, fc):
        ax.add_patch(Rectangle((x - 0.38, -i - 0.3), 0.76, 0.6, fc=fc, ec="k", zorder=3))
        ax.text(x, -i, txt, ha="center", va="center", fontsize=8, zorder=4)
    col = 0
    for i in range(n):
        box(col, i, r"RY($\pi z_%d$)" % i, "#FCF3CF")
    ax.text(col, 0.75, "angle\nencoding", ha="center", fontsize=8)
    col += 1
    for l in range(L):
        x0 = col
        for i in range(n):
            box(col, i, r"RY($\theta_{%d,%d}$)" % (l, i), "#D6EAF8")
            box(col + 1, i, r"RZ($\phi_{%d,%d}$)" % (l, i), "#D5F5E3")
        col += 2
        for i in range(n):
            t = (i + 1) % n
            ax.plot([col, col], [-i, -t], color="#6C3483", lw=1.4, zorder=2)
            ax.add_patch(Circle((col, -i), 0.09, color="#6C3483", zorder=4))
            ax.add_patch(Circle((col, -t), 0.2, fc="white", ec="#6C3483", lw=1.4, zorder=3))
            ax.plot([col - 0.2, col + 0.2], [-t, -t], color="#6C3483", lw=1.4, zorder=4)
            ax.plot([col, col], [-t - 0.2, -t + 0.2], color="#6C3483", lw=1.4, zorder=4)
            col += 1
        ax.axvspan(x0 - 0.5, col - 0.5, color="#F4F6F6", zorder=0)
        ax.text((x0 + col - 1) / 2, 0.75, "variational layer %d (RY, RZ, CNOT ring 0->1->...->%d->0)" % (l + 1, n - 1), ha="center", fontsize=8)
    for i in range(n):
        box(col, i, r"$\langle Z_%d\rangle$" % i, "#FADBD8")
    ax.text(col, 0.75, "Pauli-Z\nmeasurements", ha="center", fontsize=8)
    ax.set_title("Six-qubit variational quantum classifier  (output [B,6] -> Linear(6,1) -> logit)", fontsize=10)
    for fmt in ("png", "svg"):
        fig.savefig(str(ctx.dirs["diagrams"] / ("quantum_circuit." + fmt)), dpi=200, bbox_inches="tight")
    plt.close(fig)
    if HAVE_PENNYLANE:
        with contextlib.suppress(Exception):
            (ctx.dirs["diagrams"] / "quantum_circuit_pennylane.txt").write_text(QuantumHead(ctx.cfg.quantum, True).draw_text(), encoding="utf-8")


# =============================================================================
# AGGREGATION (all CSV outputs)
# =============================================================================
def aggregate_results(ctx: Ctx) -> dict:
    cfg, dirs = ctx.cfg, ctx.dirs
    R = {}
    frames = pd.concat(ctx.frames, ignore_index=True)
    clean_test = frames[(frames.split == "test") & (frames.condition == "clean")]
    # ----- window-level predictions -----
    wp = clean_test.copy()
    wp["pred"] = (wp.prob >= wp.thr_w).astype(int)
    wp.drop(columns=["split", "condition", "noise_type", "snr_db"]).to_csv(dirs["data"] / "window_predictions.csv", index=False)
    # ----- recording-level predictions (keeps fold) -----
    rec_fold = recording_frame(clean_test, ["seed", "fold", "model"])
    meta = ctx.rec_df.set_index("rec_idx")[["activity", "activity_group", "class_name"]]
    rec_out = rec_fold.join(meta, on="rec_idx")
    rec_out = rec_out.rename(columns={"label": "true_class", "pred": "predicted_class", "n_windows": "n_valid_windows",
                                      "thr_r": "recording_threshold"})
    rec_out["correct"] = np.where(rec_out.correct == 1, "correct", "incorrect")
    rec_out[["seed", "fold", "model", "rec_id", "class_name", "true_class", "activity", "activity_group", "n_valid_windows",
             "mean_prob", "recording_threshold", "predicted_class", "correct"]].to_csv(dirs["data"] / "recording_predictions.csv", index=False)
    R["rec_fold"], R["win_clean"] = rec_fold, wp
    # ----- fold metrics (window + recording) -----
    fm_r = recording_metrics_table(rec_fold, ["seed", "fold", "model"])
    fm_r["level"] = "recording"
    fm_w = window_metrics_table(clean_test, ["seed", "fold", "model"])
    fm_w["level"] = "window"
    fm = pd.concat([fm_r, fm_w], ignore_index=True)
    fm["mode"] = fm.model.map(lambda m: EXPERIMENTS[m]["mode"])
    fm["model_name"] = fm.model.map(lambda m: EXPERIMENTS[m]["name"])
    fm = fm.rename(columns={"n": "n_units_evaluated"})
    fm.to_csv(dirs["metrics"] / "fold_metrics.csv", index=False)
    R["fold_metrics"] = fm
    sm = summarize(fm, ["model", "mode", "level"])
    nrec = clean_test.groupby("model").rec_idx.nunique()
    s0 = sorted(clean_test.seed.unique())[0]
    nwin = clean_test[clean_test.seed == s0].groupby("model").size()
    sm["n_recordings"] = sm.model.map(nrec)
    sm["n_windows_per_seed"] = sm.model.map(nwin)
    sm.insert(1, "model_name", sm.model.map(lambda m: EXPERIMENTS[m]["name"]))
    sm.to_csv(dirs["metrics"] / "summary_metrics.csv", index=False)
    R["summary"] = sm
    # ----- pooled recording-level metrics + bootstrap CI (primary results) -----
    models = [m for m in EXPERIMENTS if m in set(rec_fold.model)]
    rec_pooled = recording_frame(clean_test, ["seed", "model"])
    def pooled_table(rp: pd.DataFrame, wpool: pd.DataFrame, tag: str) -> pd.DataFrame:
        rm = recording_metrics_table(rp, ["seed", "model"])
        g = rm.groupby("model", sort=False)
        t = g[METRIC_COLS].mean().add_suffix("").join(g[METRIC_COLS].std(ddof=1).add_suffix("_seed_std"))
        t["n_seeds"] = g.seed.nunique()
        t["n_recordings"] = g.n.first()
        t["n_healthy_recordings"], t["n_epilepsy_recordings"] = g.n_neg.first(), g.n_pos.first()
        ci, arrays, idx = bootstrap_models(rp, models, cfg.eval.n_bootstrap, cfg.eval.ci, cfg.eval.bootstrap_seed)
        t = t.reset_index().merge(ci.drop(columns=["n_recordings", "n_seeds"]), on="model", how="left")
        wm = window_metrics_table(wpool, ["seed", "model"]).groupby("model")[["balanced_accuracy", "accuracy", "roc_auc", "macro_f1"]].mean().add_prefix("window_")
        t = t.merge(wm.reset_index(), on="model", how="left")
        t["n_windows"] = t.model.map(wpool[wpool.seed == s0].groupby("model").size())
        t.insert(1, "model_name", t.model.map(lambda m: EXPERIMENTS[m]["name"]))
        t.insert(2, "mode", t.model.map(lambda m: EXPERIMENTS[m]["mode"]))
        t["subset"] = tag
        return t, arrays, idx
    rec_tbl, arrays, idx = pooled_table(rec_pooled, clean_test, "all recordings")
    rec_tbl.to_csv(dirs["metrics"] / "recording_metrics.csv", index=False)
    R["rec_tbl"] = rec_tbl
    if cfg.data.main_scope == "all":
        mask = rec_pooled.rec_idx.map(ctx.rec_df.set_index("rec_idx").activity).isin(ctx.eligible)
        wmask = clean_test.rec_idx.map(ctx.rec_df.set_index("rec_idx").activity).isin(ctx.eligible)
        sub_tbl, _, _ = pooled_table(rec_pooled[mask], clean_test[wmask], "activities present in both classes only")
        sub_tbl.to_csv(dirs["metrics"] / "recording_metrics_paired_activities_only.csv", index=False)
        R["rec_tbl_paired"] = sub_tbl
    # ----- paired comparisons: matched heads (same 6-D embedding) -----
    pairs = []
    for vq, lin, mlp, svm, nc, enc in (("E7", "E4", "E5", "E6", "E12T", "Transformer"), ("E11", "E8", "E9", "E10", "E12B", "Bi-LSTM")):
        pairs += [(vq, lin), (vq, mlp), (vq, svm), (vq, nc)]
    pairs += [("E4", "E8"), ("E5", "E9"), ("E6", "E10"), ("E7", "E11"), ("E1", "E2"), ("E1", "E3")]
    pairs += [("FT-T-vqc", "FT-T-lin"), ("FT-T-vqc", "FT-T-mlp"), ("FT-B-vqc", "FT-B-lin"), ("FT-B-vqc", "FT-B-mlp")]
    pc = paired_comparisons(arrays, idx, pairs, cfg.eval.ci)
    pc.to_csv(dirs["metrics"] / "paired_model_comparisons.csv", index=False)
    R["paired"] = pc
    # ----- comparison table -----
    fit = pd.DataFrame(ctx.fit_rows) if ctx.fit_rows else pd.DataFrame(columns=["model", "n_params", "seconds", "epochs_run", "tag"])
    outer_fit = fit[~fit.tag.astype(str).str.startswith("loao")] if "tag" in fit else fit
    fit_sum = outer_fit.groupby("model").agg(trainable_params=("n_params", "median"), mean_fit_seconds=("seconds", "mean"),
                                             mean_epochs=("epochs_run", "mean")).reset_index() if len(outer_fit) else pd.DataFrame(columns=["model"])
    ct = rec_tbl.merge(fit_sum, on="model", how="left")
    fms = sm[sm.level == "recording"].set_index("model")
    ct["fold_mean_balanced_accuracy"] = ct.model.map(fms.balanced_accuracy_mean)
    ct["fold_std_balanced_accuracy"] = ct.model.map(fms.balanced_accuracy_std)
    ct["fold_mean_accuracy"] = ct.model.map(fms.accuracy_mean)
    ct["fold_std_accuracy"] = ct.model.map(fms.accuracy_std)
    ct["n_folds_evaluated"] = ct.model.map(fms.n_folds_evaluated)
    ct["order"] = ct.model.map(lambda m: list(EXPERIMENTS).index(m))
    ct = ct.sort_values("order").drop(columns="order")
    ct.to_csv(dirs["metrics"] / "comparison_table.csv", index=False)
    R["comparison"] = ct
    fit.to_csv(dirs["metrics"] / "training_summary.csv", index=False)
    R["fit"] = fit
    # ----- activity metrics -----
    act = assign_activity_tables(ctx, rec_pooled, clean_test.assign(pred=0).drop(columns=["pred"]).pipe(lambda d: d))
    act["model_name"] = act.model.map(lambda m: EXPERIMENTS[m]["name"])
    act["mode"] = act.model.map(lambda m: EXPERIMENTS[m]["mode"])
    act.to_csv(dirs["metrics"] / "activity_metrics.csv", index=False)
    R["activity"] = act
    # ----- LOAO -----
    if ctx.loao_frames:
        lf = pd.concat(ctx.loao_frames, ignore_index=True)
        keys = ["seed", "heldout", "model"]
        lr_ = recording_metrics_table(recording_frame(lf, keys), keys)
        lr_["level"] = "recording"
        lw_ = window_metrics_table(lf, keys)
        lw_["level"] = "window"
        lm = pd.concat([lr_, lw_], ignore_index=True)
        meta_df = pd.DataFrame(ctx.loao_meta)
        lm = lm.merge(meta_df, on=["seed", "heldout"], how="left")
        lm["model_name"] = lm.model.map(lambda m: EXPERIMENTS[m]["name"])
        lm = lm.rename(columns={"heldout": "held_out_activity", "train_activities": "training_activities",
                                "n_train_rec": "n_training_recordings", "n_test_rec": "n_test_recordings",
                                "test_healthy": "healthy_test_recordings", "test_epilepsy": "epilepsy_test_recordings"})
        cols = ["seed", "held_out_activity", "training_activities", "n_training_recordings", "n_val_rec", "n_test_recordings",
                "healthy_test_recordings", "epilepsy_test_recordings", "model", "model_name", "level"] + METRIC_COLS
        lm[cols].to_csv(dirs["metrics"] / "activity_holdout_metrics.csv", index=False)
        g = lm.groupby(["model", "level", "held_out_activity"], sort=False)
        hs = g[METRIC_COLS].mean().add_suffix("_mean").join(g[METRIC_COLS].std(ddof=1).add_suffix("_std")).reset_index()
        hs = hs.rename(columns={"held_out_activity": "heldout"})
        hs.to_csv(dirs["metrics"] / "activity_holdout_summary.csv", index=False)
        R["loao"], R["loao_summary"] = lm, hs
        R["loao_frames"] = lf
        lf_rec = recording_frame(lf, ["seed", "heldout", "model"])
        lf_rec.to_csv(dirs["data"] / "loao_recording_predictions.csv", index=False)
    # ----- noise -----
    nz = frames[(frames.split == "test") & (frames.noise_type.fillna("") != "")]
    if len(nz):
        seeds_n = sorted(nz.seed.unique())
        nf = frames[(frames.split == "test") & frames.seed.isin(seeds_n)].copy()
        nf["noise_type"] = nf.noise_type.fillna("").replace("", "clean")
        nf["snr_db"] = nf.snr_db.fillna(1e9)
        nf["condition"] = nf.condition.replace("clean", "clean")
        nt = noise_tables(ctx, nf)
        nt["model_name"] = nt.model.map(lambda m: EXPERIMENTS[m]["name"])
        nt["mode"] = nt.model.map(lambda m: EXPERIMENTS[m]["mode"])
        nt.to_csv(dirs["metrics"] / "noise_robustness_metrics.csv", index=False)
        R["noise"] = nt
        nrec = recording_frame(nf, ["seed", "fold", "model", "condition", "noise_type", "snr_db"])
        nrec = nrec.join(meta, on="rec_idx")
        nrec.to_csv(dirs["data"] / "noise_recording_predictions.csv", index=False)
    return R


# =============================================================================
# REPORTS
# =============================================================================
def _fmt_ci(r, m="balanced_accuracy"):
    v, lo, hi = r.get(m, np.nan), r.get(m + "_ci_low", np.nan), r.get(m + "_ci_high", np.nan)
    if not np.isfinite(v):
        return "n/a"
    return "%.3f [%.3f, %.3f]" % (v, lo, hi) if np.isfinite(lo) else "%.3f" % v


def write_dataset_audit_report(ctx: Ctx) -> None:
    a, man = ctx.audit, ctx.man_full
    L = a["length_analysis"]
    cnt = man.groupby(["activity", "class_name"]).size().unstack(fill_value=0).reset_index()
    cnt["both_classes"] = cnt.apply(lambda r: "yes" if r.get("Healthy Individuals", 0) > 0 and r.get("Epileptic Patients", 0) > 0 else "no", axis=1)
    lines = ["# Dataset audit report", "",
             "Data source: `%s` (%s). Generated automatically by `hybrid_quantum_eeg_epilepsy.py`." % (a["data_source"], a["source_kind"]), "",
             "## 1. Inventory", "",
             "| Item | Documented | Found |", "|---|---|---|",
             "| CSV recordings | %d | %d |" % (a["documented"]["files"], a["found"]["csv_files"]),
             "| Healthy recordings | %d | %d |" % (a["documented"]["healthy"], a["found"]["healthy"]),
             "| Epilepsy recordings | %d | %d |" % (a["documented"]["epilepsy"], a["found"]["epilepsy"]),
             "| Samples per recording | %d | %s |" % (a["documented"]["expected_samples"], L["length_counts"]),
             "| Recordings excluded from modelling | - | %d |" % a["found"]["excluded"], "",
             "Recordings excluded (with reasons): %s" % (a["exclusions"] or "none"), "",
             "## 2. Activity coverage (from normalised file names)", "", df_to_md(cnt),
             "Activities present in both classes (used for activity-transfer experiments): **%s**." % ", ".join(a["eligible_activities_both_classes"]),
             "Healthy-only activities (never used in binary activity-transfer experiments): %s." % ", ".join(a["single_class_activities_excluded_from_transfer"]), "",
             "Unknown/unnormalised activity names: %s." % (a["found"]["unknown_activity_names"] or "none"), "",
             "ReadMe code (00/01/02) vs name-based group mismatches: %d." % a["readme_code_check"]["n_mismatches"], "",
             "## 3. Length discrepancy (10,241 vs documented 10,240 samples)", "",
             "- Length histogram: %s" % L["length_counts"],
             "- All recordings share the same length: **%s**; excess over documentation: **%d sample(s)**." % (L["all_recordings_same_length"], L["excess_vs_expected"]),
             "- Header rows: %d files; files whose last sample equals the previous sample: %d; files whose first two samples are equal: %d." % (
                 L["n_files_header_present"], L["n_files_last_equals_previous_sample"], L["n_files_first_equals_second_sample"]),
             "- Formatting quirk: %d file(s) carry trailing commas on every row: %s" % (L["n_files_trailing_delimiter"], L["files_trailing_delimiter"]),
             "", "**Interpretation (inference, not proof).** " + L["interpretation"], "",
             "**Policy used:** `%s`. %s" % (L["policy"], L["policy_explanation"]), "",
             "With non-overlapping 5 s windows (2,560 samples) a 10,241-sample recording yields 4 complete windows and 1 unused trailing sample "
             "(logged per recording in `data/recording_metadata.csv`, column `leftover_samples`). Nothing is silently truncated: the policy is configurable "
             "(`data.length_policy`).", "",
             "## 4. Signal-quality checks", "",
             "- Global amplitude range: [%.3f, %.3f]; median per-recording std %.3f. %s" % (a["amplitude"]["global_min"], a["amplitude"]["global_max"],
                                                                                          a["amplitude"]["median_recording_std"], a["amplitude"]["note"]),
             "- Constant recordings: %s" % (a["constant_recordings"] or "none"),
             "- Duplicate recordings (identical samples): %s" % (a["duplicates"]["pairs"] or "none"),
             "- Recordings with unusual standard deviation (|robust z| > 6): %s" % (a["unusual_std_recordings"] or "none"),
             "- Saturation fraction (samples at the global min/max): median %.4f, max %.4f (per recording in the manifest)." % (
                 man.saturation_fraction_global_extremes.median(), man.saturation_fraction_global_extremes.max()), "",
             "## 5. Participant identity", "", a["participant_id_warning"], "",
             "## 6. Files", "", "- `config/dataset_manifest.csv` - one row per CSV with all audit fields.",
             "- `config/dataset_audit.json` - machine-readable audit.", ""]
    (ctx.dirs["reports"] / "dataset_audit_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_methodology_report(ctx: Ctx, inv: dict, selftests: dict, grad: dict) -> None:
    c = ctx.cfg
    w = ctx.wosg_summary
    L = ["# Methodology report", "",
         "Profile: **%s**; seeds: %s; outer folds: %d (run: %s); device: %s." % (c.profile, c.run.seeds, c.run.n_folds,
                                                                                c.run.max_folds or "all", ctx.device), "",
         "## 1. Preprocessing - WOSG (published algorithm vs implementation assumptions)", "",
         "**Published structure** (Gajbhiye et al., IEEE Trans. Instrum. Meas. 2021, as cited by the base paper): discrete wavelet transform; "
         "an optimised Savitzky-Golay (SG) filter is applied to the artefact-contaminated *approximation* sub-band; the SG output (artefact estimate) is "
         "subtracted from the approximation; the filtered EEG is the inverse DWT of the cleaned approximation plus the unchanged detail sub-bands.", "",
         "**Not available to this implementation (neither in the base paper nor in the accessible abstract of the cited paper)**: wavelet family, decomposition "
         "level, SG window length, SG polynomial order and the optimisation criterion. Therefore:", "",
         "- wavelet = `%s`, level = %d (approximation band 0-%.2f Hz at 512 Hz), mode = `%s` (**assumption**);" % (c.wosg.wavelet, c.wosg.level, 512 / 2 ** (c.wosg.level + 1), c.wosg.mode),
         "- SG (window, order) is chosen **per recording** by grid search over windows %s and orders %s minimising "
         "`J = P_low(clean)/P_low(raw) + %.1f * (1 - corr_in-band)` (power below %.1f Hz vs correlation within %s Hz). "
         "This is an **unsupervised proxy objective of this project - not the criterion of the original paper**;" % (
             c.wosg.window_candidates, c.wosg.polyorder_candidates, c.wosg.lambda_inband, c.wosg.lowfreq_cut_hz, c.wosg.inband_hz),
         "- the filter is applied to the whole recording before segmentation, as in the base-paper flow chart; a Butterworth filter is NOT used as a substitute.", "",
         "Observed effect on this dataset: median low-frequency (<0.5 Hz) power ratio raw/filtered = %.1f; chosen (window, order) counts: %s." % (
             w["median_lowfreq_power_ratio"], w["chosen_parameter_counts"]), "",
         "## 2. Segmentation", "",
         "5 s windows at 512 Hz = 2,560 samples, overlap %.0f%% (hop %d). Recording ID, class, activity and window index are stored for every window "
         "(`data/window_metadata.csv`). Windows of one recording are never split across train/validation/test." % (100 * c.window.overlap, ctx.hop), "",
         "## 3. GWST", "",
         "Implemented from Eq. (1)-(3) of the base paper (standard S-transform with Gaussian window `exp(-2 pi^2 m^2 / k^2)`, periodic/symmetric in m). "
         "%d voices equally spaced in %.1f-%.1f Hz. Since the 0.2 Hz DFT grid does not contain these voices, Z(m+k) is evaluated **exactly** for fractional k via a "
         "frequency-shifted DFT (no interpolation). Verified against a direct O(N^2) evaluation of the definition (max abs error %.2e) and by localising a 10 Hz sine at %.2f Hz. "
         "Not STFT, not CWT." % (ctx.n_freq, c.gwst.fmin, c.gwst.fmax, selftests["gwst_vs_direct_definition_max_abs_error"], selftests["gwst_peak_frequency_of_10Hz_sine"]),
         "Ambiguity: the paper's 'histogram bin size of 10' is implemented as **10 equal-width bins**; its '225 frequency components' is implemented as 225 equally spaced voices.", "",
         "## 4. Handcrafted baseline", "",
         "L1 norm (sum over time of |GWST| per frequency) and Shannon entropy (bits; 10-bin normalised histogram; 0 log 0 := 0) -> 450-D vector (asserted). "
         "E1 Random Forest, E2 SVM, E3 mutual-information selection (fitted on the training partition only) + Random Forest. Hyper-parameters (grids in config) are "
         "selected by validation log-loss; models are fitted on the training partition only (identical label budget to the neural models).", "",
         "## 5. Temporal representation and encoders", "",
         "`log(1 + |GWST|/a0)`, a0 = median over training windows and frequencies of the per-window mean |GWST| (training data only); mean-pooling of 40 consecutive samples -> 64 tokens; "
         "per-frequency standardisation with training statistics; Linear(F=%d -> 32). Token tensor per window: [64, %d]; encoder input [B, 64, 32]." % (ctx.n_freq, ctx.n_freq), "",
         "- **Transformer**: sinusoidal positional encoding, 2 pre-norm blocks, 4 heads, FF 64, GELU, dropout 0.1, residuals, temporal attention pooling -> [B,32].",
         "- **Bi-LSTM**: 1 layer, 16 hidden units per direction, dropout 0.1, temporal attention pooling -> [B,32].",
         "- **Shared embedding**: LayerNorm(32) -> Linear(32,6) -> Tanh.", "",
         "Parameter counts:", "", "```json", json.dumps(inv, indent=2, default=json_default), "```", "",
         "## 6. Heads on the SAME 6-D embedding", "",
         "Linear(6,1); MLP 6-6-1 (Tanh); RBF-SVM (C, gamma chosen on validation log-loss); six-qubit VQC (PennyLane `default.qubit`, torch interface, backprop): |0>^6 -> RY(pi z_i) -> "
         "2 x [RY, RZ on every qubit -> CNOT ring 0->1->2->3->4->5->0] -> <Z_i> -> Linear(6,1). "
         "Interpretation of the specification: the CNOT ring is applied after the rotations **inside each variational layer**. E12 removes the CNOT ring only.",
         "Gradient check (Transformer and Bi-LSTM): all gradient norms non-zero = **%s** (`config/gradient_check.json`)." % grad.get("passed"), "",
         "**Frozen-encoder protocol (primary).** For every (seed, fold) each encoder is first trained end-to-end with a %s head (BCE-with-logits, AdamW, early stopping on validation loss) to produce the embedding; "
         "the encoder is then frozen and all heads are trained/fitted on the identical embeddings of the identical training windows. **Caveat:** the embedding was optimised for the pre-training head "
         "(`model.encoder_pretrain_head` = %s), which can favour that head type in the frozen comparison. The separate **end-to-end fine-tuning** comparison (FT-*) starts from the same pre-trained "
         "encoder and trains each head jointly; it is reported in its own table and is never mixed with frozen results." % (c.model.encoder_pretrain_head, c.model.encoder_pretrain_head), "",
         "## 7. Training configuration", "", "```json", json.dumps(dict(c.train), indent=2), "```", "",
         "No hyper-parameter search is run on neural models unless `train.encoder_lr_grid` / `train.head_lr_grid` are set; validation-based grids exist only for the sklearn models (see config). "
         "This asymmetry (grid-tuned SVM/RF vs fixed-lr networks) is a limitation of the comparison.", "",
         "## 8. Data splitting and leakage control", "",
         "Outer: %d-fold `StratifiedGroupKFold` over windows with **recording** as the group (shuffled with the experiment seed). Inner: a recording-level validation partition (1/%d of the training recordings) "
         "for early stopping, model selection and thresholds. Test recordings are used only for evaluation. Fold assignments: `config/fold_assignments.csv`. "
         "If a valid grouped stratified split cannot be built the run stops. **No participant IDs exist**: splits are recording-level, multiple recordings may come from the same person, so "
         "no participant-independent generalisation is claimed." % (c.run.n_folds, c.cv.inner_val_splits), "",
         "## 9. Recording-level prediction", "",
         "Window probabilities are averaged per recording; the recording-level threshold maximises balanced accuracy on **validation recordings only** (ties -> closest to 0.5; falls back to 0.5 if validation has one class). "
         "A separate window-level threshold is selected on validation windows. Recording-level metrics are primary.", "",
         "## 10. Activity and noise robustness", "",
         "Activity-wise / group metrics come from pooled outer-CV test predictions. Leave-one-activity-out trains on the other eligible activities (complete recordings, validation partition drawn from them) and tests on the held-out activity "
         "(eligible activities: %s)." % ", ".join(ctx.eligible),
         "Noise: synthetic corruption of **test recordings only** before the (identical) WOSG/GWST pipeline; trained models, normalisation and thresholds are unchanged. "
         "SNR reference: variance of the %s recording; deterministic generators seeded by (noise seed, recording, type, SNR). "
         "**This is a controlled robustness experiment with synthetic signals; it does not show performance under real motion, EMG or ocular artefacts, and the synthetic EMG/ocular-like signals are not recorded artefacts.**" % c.noise.snr_reference, "",
         "## 11. Statistics", "",
         "Bootstrap (%d replicates, %.0f%% percentile CI) resamples **complete recordings** (the same resample for all seeds, metrics averaged over seeds). Paired differences between models use the same resamples; exact McNemar tests are reported per seed. "
         "No multiplicity correction is applied: all comparisons are exploratory. Fold-level mean +/- std use (seed, fold) pairs, which are not independent samples.", "",
         "## 12. Self-tests", "", "```json", json.dumps(selftests, indent=2, default=json_default), "```", ""]
    (ctx.dirs["reports"] / "methodology_report.md").write_text("\n".join(L), encoding="utf-8")


def interpret(ctx: Ctx, R: dict) -> list[str]:
    """Data-driven, deliberately cautious interpretation statements."""
    out = []
    ct = R["comparison"].set_index("model")
    pc = R["paired"]
    fr = ct[ct["mode"] != "end-to-end"]
    if len(fr):
        best = fr.balanced_accuracy.idxmax()
        out.append("Highest pooled recording-level balanced accuracy among frozen/classical models: **%s (%s)** = %s. Differences between nearby models are usually "
                   "within the bootstrap CIs (n = %d recordings), so this ranking is not a statistically established order." % (
                       best, SHORT[best], _fmt_ci(ct.loc[best]), int(ct.loc[best].n_recordings)))
    for vq, nm in (("E7", "Transformer"), ("E11", "Bi-LSTM")):
        sub = pc[(pc.model_a == vq) & (pc.metric == "balanced_accuracy")]
        for _, r in sub.iterrows():
            d = r.mean_difference_a_minus_b
            if not np.isfinite(r.ci_low):
                continue
            verdict = ("VQC higher" if d > 0 else "VQC lower") + " and the CI excludes 0" if r.ci_excludes_zero else "no distinguishable difference (CI includes 0)"
            out.append("%s head, VQC (%s) minus %s (%s), recording-level balanced accuracy: %+.3f [%+.3f, %+.3f] -> %s." % (
                nm, vq, r.model_b, SHORT.get(r.model_b, r.model_b), d, r.ci_low, r.ci_high, verdict))
    if "E7" in ct.index and "E5" in ct.index and "mean_fit_seconds" in ct:
        out.append("Cost: VQC head trainable parameters = %s vs MLP head = %s; mean head fitting time %.1f s (VQC, classical simulation) vs %.1f s (MLP). "
                   "Simulation overhead is not evidence about quantum hardware." % (ct.loc["E7"].get("trainable_params"), ct.loc["E5"].get("trainable_params"),
                                                                             ct.loc["E7"].get("mean_fit_seconds", np.nan), ct.loc["E5"].get("mean_fit_seconds", np.nan)))
    out.append("The 6-D embedding for the frozen comparison was pre-trained with a %s head; heads of that type may be favoured." % ctx.cfg.model.encoder_pretrain_head)
    any_adv = bool(len(pc[(pc.metric == "balanced_accuracy") & pc.ci_excludes_zero & pc.model_a.isin(["E7", "E11", "FT-T-vqc", "FT-B-vqc"]) & (pc.mean_difference_a_minus_b > 0)]))
    out.append("**Quantum-advantage statement:** this study simulates a 6-qubit circuit on a classical machine and compares it with matched classical heads on one small dataset. "
               + ("In at least one paired comparison the VQC point estimate is higher with a CI excluding 0; this is exploratory, uncorrected for multiple comparisons, and does not establish quantum advantage."
                  if any_adv else "No paired comparison shows the VQC to be better than a matched classical head with a CI excluding 0. In no case is quantum advantage or supremacy claimed."))
    return out


def md_primary_table(rec_tbl: pd.DataFrame, fam: str) -> str:
    d = rec_tbl.copy()
    d["is_ft"] = d.model.map(lambda m: EXPERIMENTS[m]["family"] == "finetune")
    d = d[d.is_ft == (fam == "finetune")]
    d["order"] = d.model.map(lambda m: list(EXPERIMENTS).index(m))
    d = d.sort_values("order")
    t = pd.DataFrame({"ID": d.model, "Model": d.model_name, "Bal. acc. [95% CI]": [_fmt_ci(r) for _, r in d.iterrows()],
                      "Accuracy [95% CI]": [_fmt_ci(r, "accuracy") for _, r in d.iterrows()],
                      "Sensitivity": d.sensitivity.values, "Specificity": d.specificity.values,
                      "ROC-AUC": d.roc_auc.values, "MCC": d.mcc.values,
                      "Window bal. acc.": d.window_balanced_accuracy.values})
    return df_to_md(t, "%.3f")


def write_final_report(ctx: Ctx, R: dict, notes: list[str]) -> None:
    c = ctx.cfg
    rt, sm = R["rec_tbl"], R["summary"]
    s_rec = sm[sm.level == "recording"]
    fold_tbl = pd.DataFrame({"ID": s_rec.model, "Model": s_rec.model_name, "mode": s_rec["mode"],
                             "folds evaluated": s_rec.n_folds_evaluated,
                             "Bal. acc. (mean ± sd over folds)": [fmt_ms(a, b) for a, b in zip(s_rec.balanced_accuracy_mean, s_rec.balanced_accuracy_std)],
                             "Accuracy (mean ± sd)": [fmt_ms(a, b) for a, b in zip(s_rec.accuracy_mean, s_rec.accuracy_std)],
                             "Macro-F1": s_rec.macro_f1_mean.values, "ROC-AUC (valid folds)": s_rec.roc_auc_mean.values,
                             "ROC-AUC n valid": s_rec.roc_auc_n_valid.values})
    L = ["# Final experiment report", "",
         "> Auto-generated from the numbers produced in this run. Nothing in this report is hard-coded or taken from the base paper. "
         "Profile: **%s**, seeds %s, %d outer folds%s." % (c.profile, c.run.seeds, c.run.n_folds,
                                                          " (restricted to %d)" % c.run.max_folds if c.run.max_folds else ""), "",
         "## 1. What was run", "",
         "- Dataset: %d recordings (%d healthy / %d epilepsy), %d windows of 5 s (%s)." % (
             len(ctx.rec_df), (ctx.rec_df.label == 0).sum(), (ctx.rec_df.label == 1).sum(), len(ctx.win_df), "non-overlapping" if c.window.overlap == 0 else "overlap %.2f" % c.window.overlap),
         "- Evaluation unit: **recording** (mean of window probabilities, validation-selected threshold). Window-level metrics are secondary.",
         "- Splits: grouped by recording (no participant IDs exist -> **no participant-independent claim**).",
         "- Experiments: %s." % ", ".join(sorted(set(rt.model), key=lambda m: list(EXPERIMENTS).index(m))), "",
         "## 2. Primary results - recording level, frozen encoders and classical baselines", "",
         "Pooled over all outer test folds, averaged over %d seed(s); CI = %.0f%% bootstrap over recordings. All models share identical folds, partitions and (for E4-E12) identical 6-D embeddings." % (
             int(rt.n_seeds.max()), 100 * c.eval.ci), "", md_primary_table(rt, "frozen"),
         "Fold-wise mean ± sd (n = seeds x folds; NaN-aware):", "", df_to_md(fold_tbl[fold_tbl["mode"] != "end-to-end"].drop(columns="mode"), "%.3f"),
         "## 3. End-to-end fine-tuned models (separate comparison - not comparable 1:1 with Section 2)", "",
         md_primary_table(rt, "finetune") if (rt.model.map(lambda m: EXPERIMENTS[m]["family"] == "finetune")).any() else "_not run in this profile_\n", ""]
    if "rec_tbl_paired" in R:
        L += ["## 4. Primary results restricted to activities present in both classes", "", md_primary_table(R["rec_tbl_paired"], "frozen"), ""]
    pc = R["paired"]
    L += ["## 5. Matched classical-vs-quantum comparison (same embeddings)", "",
          "Difference = model_a - model_b in recording-level metric; CI from paired bootstrap over recordings; McNemar exact p per seed (uncorrected, exploratory).", "",
          df_to_md(pc[pc.metric == "balanced_accuracy"][["model_a", "model_b", "mean_difference_a_minus_b", "ci_low", "ci_high", "ci_excludes_zero",
                                                         "mcnemar_a_only_correct", "mcnemar_b_only_correct", "mcnemar_exact_p_per_seed"]], "%.3f"), ""]
    act = R.get("activity")
    if act is not None and len(act):
        a = act[(act.level == "recording") & (act.unit_type != "paired_activities_all") & act.model.isin([m for m in ["E1", "E2", "E5", "E7", "E9", "E11"]])]
        pv = a.pivot_table(index="unit", columns="model", values="accuracy_mean")
        L += ["## 6. Activity-wise and activity-group results (recording-level accuracy; pooled outer-CV test predictions)", "",
              "Per-activity sample sizes are tiny (2-10 recordings per class); treat as descriptive. Healthy-only activities can only yield accuracy = specificity.", "",
              df_to_md(pv.reset_index(), "%.3f"), ""]
    if "loao_summary" in R:
        hs = R["loao_summary"]
        pv = hs[hs.level == "recording"].pivot_table(index="heldout", columns="model", values="balanced_accuracy_mean")
        L += ["## 7. Leave-one-activity-out (recording-level balanced accuracy)", "",
              "Train on the other eligible activities, test on the held-out activity (complete recordings; validation partition drawn from training activities only).", "",
              df_to_md(pv.reset_index(), "%.3f"), "Full table: `metrics/activity_holdout_metrics.csv`.", ""]
    if "noise" in R:
        nt = R["noise"]
        d = nt[(nt.level == "recording") & (nt.noise_type != "clean")]
        pv = d.pivot_table(index=["noise_type", "snr_db"], columns="model", values="delta_balanced_accuracy_vs_clean").reset_index()
        L += ["## 8. Synthetic-corruption robustness (change in recording-level balanced accuracy vs clean)", "",
              "Controlled experiment with **synthetic** corruptions; it does not prove behaviour under real motion/EMG/ocular artefacts.", "", df_to_md(pv, "%+.3f"), ""]
    fit = R["fit"]
    if len(fit):
        ft = fit[~fit.tag.astype(str).str.startswith("loao")].groupby("model").agg(params=("n_params", "median"), seconds=("seconds", "mean"), epochs=("epochs_run", "mean")).reset_index()
        L += ["## 9. Training cost", "", df_to_md(ft, "%.1f"), ""]
    L += ["## 10. Interpretation (data-driven; see also results_interpretation.md)", ""] + ["- " + n for n in notes] + [
        "", "## 11. Limitations", "",
        "- 90 recordings (30 epilepsy); folds contain ~6 epilepsy recordings, so every estimate has wide uncertainty.",
        "- No participant IDs: recording-level grouping cannot exclude person-level leakage; results are **not** participant-independent.",
        "- Healthy-only activities (standing, TV, cooking, jumping) can act as shortcuts in the main CV; see the paired-activities-only table.",
        "- WOSG parameters/criterion and the exact GWST implementation details of the base paper are not published; assumptions are listed in the methodology report.",
        "- Quantum models are classically simulated; no hardware, noise or shot-noise effects are evaluated.",
        "- Fixed learning rates for neural models; only sklearn models are grid-tuned.",
        "- Synthetic corruptions are not real artefacts.", "",
        "## 12. Output index", "",
        "`config/` configuration, environment, audit, folds; `data/` features and predictions; `metrics/` all CSV tables; `plots/`; `diagrams/`; `checkpoints/`; `logs/`.", ""]
    (ctx.dirs["reports"] / "final_experiment_report.md").write_text("\n".join(L), encoding="utf-8")
    (ctx.dirs["reports"] / "results_interpretation.md").write_text(
        "# Results interpretation\n\nAutomatically derived, intentionally conservative statements (profile `%s`).\n\n%s\n\n"
        "## Reading guide\n\n- Prefer recording-level metrics; window-level numbers are correlated within recordings.\n"
        "- Compare VQC only with heads on the same embedding (E7 vs E4/E5/E6/E12T; E11 vs E8/E9/E10/E12B).\n"
        "- A CI that includes 0 means the data do not distinguish the models.\n"
        "- Fine-tuned results are a different protocol and must not be ranked against frozen results.\n" % (c.profile, "\n".join("- " + n for n in notes)),
        encoding="utf-8")


def write_base_paper_comparison(ctx: Ctx, R: dict) -> None:
    c = ctx.cfg
    ct = R["comparison"].set_index("model")
    def g(m):
        return _fmt_ci(ct.loc[m]) if m in ct.index else "n/a"
    L = ["# Comparison with the base paper", "",
         "Base paper: Dash S., Dash D.K., Tripathy R.K., Pachori R.B., *Time-frequency domain machine learning for detection of epilepsy using wearable EEG sensor signals recorded during physical activities*, "
         "Biomedical Signal Processing and Control 100 (2025) 107041.", "",
         "## 1. Comparison table", "",
         "| Aspect | Base paper | Proposed project |", "|---|---|---|",
         "| Input | Wearable FP1 EEG | Same dataset source, FP1, 512 Hz |",
         "| Preprocessing | WOSG | WOSG reproduction (structure published; wavelet/level/SG parameters and optimisation criterion are assumptions) |",
         "| Segmentation | 5 seconds | 5 seconds (2,560 samples), non-overlapping (configurable overlap) |",
         "| TF transform | GWST | GWST (Eq. 1-3), 0.5-50 Hz, %d voices, exact fractional-k evaluation |" % ctx.n_freq,
         "| Handcrafted features | L1 + Shannon entropy | Reproduced 450-D baseline (E1-E3) |",
         "| Feature learning | Existing ML/DL models | Temporal GWST tokens + Transformer and Bi-LSTM (independent) |",
         "| Quantum component | Not used | Six-qubit VQC (E7, E11) + no-CNOT ablation (E12) |",
         "| Classical control | Existing classifiers | Matched linear / MLP / RBF-SVM heads on identical 6-D embeddings |",
         "| Activity evaluation | Published activity protocols | Activity-wise, group-wise and leave-one-activity-out |",
         "| Artifact robustness | Original evaluation | Controlled synthetic corruption (Gaussian, drift, EMG-like, ocular-like; 20/10/5 dB) |",
         "| Prediction level | Reported frame-based evaluation | Window and recording-level (primary) |", "",
         "## 2. Point-by-point", "",
         "1. **Same dataset source** - the public wearable-EEG ADL dataset (NeuroSky MindWave 2.0).",
         "2. **Same FP1 single-channel context**; 3. **same 512 Hz** sampling.",
         "4. **WOSG intention** is kept (DWT -> SG on the approximation -> subtraction). Exact parameters are unpublished -> documented assumptions, per-recording SG optimisation by an unsupervised proxy objective.",
         "5. **Five-second segmentation** and 7. **0.5-50 Hz** range are reproduced; 6. **GWST** is implemented from the paper's equations.",
         "8. **L1 + Shannon entropy** baseline: 450-D vectors, RF/SVM and MI-selected RF are reproduced as E1-E3.",
         "9-11. **Additional**: temporal log-GWST tokens, Transformer vs Bi-LSTM encoders, 6-D learned bottleneck.",
         "12-13. **Six-qubit VQC** compared with matched classical heads on identical embeddings.",
         "14. **Activity-held-out robustness**, 15. **synthetic artefact robustness**, 16. **recording-level prediction** are new evaluations.", "",
         "## 3. Published reference values (quoted from the paper, NOT produced by this code)", "",
         "| Item | Published value |", "|---|---|",
         "| Random Forest, GWST L1+entropy, hold-out validation (70/10/20 frames) | 90.74 % accuracy |",
         "| Multi-layer LSTM, 10-fold CV | 74.44 % average accuracy |",
         "| Multi-layer LSTM, jogging / running / idle sitting activity-specific | 82.72 % / 82.41 % / 87.30 % |", "",
         "These numbers use the paper's own protocol (frame-based splits) and **cannot be compared directly** with this project's recording-grouped results. Our corresponding values from this run (recording-level, pooled outer CV, balanced accuracy [95%% CI]): "
         "E1 RF %s; E2 SVM %s." % (g("E1"), g("E2")), "",
         "## 4. Discrepancies and caveats found while reproducing", "",
         "- **Recording counts.** The paper text states 60 healthy and 30 epilepsy recordings in the database but also that 30 healthy + 30 epilepsy recordings were used. The archive contains 60 healthy + 30 epilepsy files "
         "(this project uses all 90 in the main CV and reports a subset restricted to activities present in both classes).",
         "- **Frame count.** The paper reports 540 frames for 5 s windows (and 3000 / 1440 / 960 / 660 for 1-4 s) with a stated total of 45 minutes. 60 recordings x 20 s = 20 min would give 240 non-overlapping 5 s frames, "
         "and the 90 files give %d. The 540 figure therefore cannot be reproduced with non-overlapping windows from the archive; the paper does not state an overlap, so the reason (overlap, different data, counting) is unknown." % len(ctx.win_df),
         "- **Window length.** Each CSV has 10,241 rows instead of the documented 10,240 (see dataset audit).",
         "- **Frame-level splitting.** The paper evaluates frames with 70/10/20 hold-out and 10-fold CV and mentions subject-specific selection, but does not state recording-level grouping for the wearable database. If frames from the same recording "
         "appear in training and test partitions, accuracy can be inflated by within-recording leakage. This is a possibility to check with the authors, not a verified finding. This project prevents it by construction.",
         "- **Subject independence.** The archive has no participant IDs; neither this project nor (as far as the available description shows) the archive allows verifying participant-independent evaluation.",
         "- **Histogram 'bin size of 10'** and **225 frequency components** are interpreted as 10 bins and 225 voices; WOSG parameters are not given in the paper.",
         "- **Hyper-parameters.** The paper's grid search (Table 1) selects on the validation set; this project also selects on validation recordings only.", ""]
    (ctx.dirs["reports"] / "comparison_with_base_paper.md").write_text("\n".join(L), encoding="utf-8")


# =============================================================================
# MAIN
# =============================================================================
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Hybrid quantum-classical EEG epilepsy detection (research pipeline)")
    ap.add_argument("--profile", default=os.environ.get("EEG_PROFILE", "full"), choices=list(PROFILES))
    ap.add_argument("--data-path", default=None)
    ap.add_argument("--output-root", default=OUTPUT_ROOT)
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-folds", type=int, default=None)
    ap.add_argument("--max-folds", type=int, default=None)
    ap.add_argument("--device", default=None, choices=["auto", "cpu", "cuda"])
    ap.add_argument("--length-policy", default=None, choices=["keep_filter_drop_incomplete", "trim_to_nominal", "strict"])
    ap.add_argument("--main-scope", default=None, choices=["all", "paired"])
    ap.add_argument("--no-finetune", action="store_true")
    ap.add_argument("--no-loao", action="store_true")
    ap.add_argument("--no-noise", action="store_true")
    ap.add_argument("--no-quantum", action="store_true", help="explicitly omit VQC experiments (they are then absent, never replaced)")
    ap.add_argument("--keep-cache", action="store_true", help="keep the GWST magnitude cache (~0.8 GB)")
    ap.add_argument("--config-json", default=None, help="JSON file with config overrides (nested dict)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    ov = {}
    if args.config_json:
        ov = json.load(open(args.config_json))
    ov = deep_update(ov, {"data": {}, "run": {}})
    if args.data_path:
        ov["data"]["path"] = args.data_path
    if args.length_policy:
        ov["data"]["length_policy"] = args.length_policy
    if args.main_scope:
        ov["data"]["main_scope"] = args.main_scope
    if args.seeds:
        ov["run"]["seeds"] = args.seeds
    if args.n_folds:
        ov["run"]["n_folds"] = args.n_folds
    if args.max_folds:
        ov["run"]["max_folds"] = args.max_folds
    if args.device:
        ov["run"]["device"] = args.device
    for flag, key in ((args.no_finetune, "run_finetune"), (args.no_loao, "run_loao"), (args.no_noise, "run_noise"), (args.no_quantum, "run_quantum")):
        if flag:
            ov["run"][key] = False
    cfg = build_config(args.profile, ov)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    root = Path(args.output_root) / ("experiment_" + ts)
    n = 1
    while root.exists():                                  # never overwrite a previous experiment
        n += 1
        root = Path(args.output_root) / ("experiment_%s_%d" % (ts, n))
    dirs = make_dirs(root)
    setup_logging(dirs["logs"])
    ctx = Ctx()
    ctx.cfg, ctx.dirs = cfg, dirs
    ctx.best_enc, ctx.fit_rows, ctx.histories, ctx.frames, ctx.loao_frames, ctx.loao_meta = {}, [], [], [], [], []
    t_start = time.time()
    LOG.info("Experiment directory: %s", root)
    try:
        with stage("0 Setup: configuration, environment, device"):
            torch.set_num_threads(int(cfg.run.num_threads))
            ctx.device = pick_device(cfg.run.device)
            save_json(dict(cfg), dirs["config"] / "config.json")
            env = environment_info(ctx.device)
            save_json(env, dirs["config"] / "environment.json")
            LOG.info("Environment: python %s | torch %s | pennylane %s | device %s | CUDA %s",
                     platform.python_version(), torch.__version__, env["pennylane_version"], ctx.device, env["cuda_available"])
            if cfg.run.run_quantum and cfg.run.run_encoders and not HAVE_PENNYLANE:
                raise DependencyError("PennyLane is not available (%s). Install it (`pip install pennylane`) or run with --no-quantum "
                                      "to omit the VQC experiments explicitly. No classical layer is substituted." % PENNYLANE_ERROR)
        with stage("1 Self-tests and quantum gradient verification"):
            selftests = run_self_tests(cfg, ctx.device)
            save_json(selftests, dirs["config"] / "selftests.json")
            grad = {"passed": None, "note": "quantum experiments disabled"}
            if HAVE_PENNYLANE and cfg.run.run_quantum:
                grad = verify_quantum_gradients(cfg, int(cfg.gwst.n_freq), ctx.device)
                LOG.info("Gradient check: %s", json.dumps(grad, default=json_default))
                if not grad["passed"]:
                    raise RuntimeError("Gradients do not propagate through the full quantum model: %s" % grad)
            save_json(grad, dirs["config"] / "gradient_check.json")
            inv = model_inventory(cfg, int(cfg.gwst.n_freq))
            save_json(inv, dirs["config"] / "model_parameter_counts.json")
        with stage("2 Dataset audit"):
            signals, man, audit = load_dataset(cfg, cfg.data.path)
            ctx.man_full, ctx.audit = man, audit
            man.to_csv(dirs["config"] / "dataset_manifest.csv", index=False)
            save_json(audit, dirs["config"] / "dataset_audit.json")
            ctx.man_used = man[~man.excluded].copy()
            write_dataset_audit_report(ctx)
        with stage("3 WOSG filtering"):
            ctx.raw_used, ctx.filt, ctx.wosg_info = filter_all_recordings(signals, cfg)
            ratios = [(_lowpower(ctx.raw_used[r], cfg.data.fs, cfg.wosg.lowfreq_cut_hz) + 1e-18) / (_lowpower(ctx.filt[r], cfg.data.fs, cfg.wosg.lowfreq_cut_hz) + 1e-18)
                      for r in ctx.filt]
            cnt = Counter("w%s_p%s" % (v.get("window"), v.get("polyorder")) for v in ctx.wosg_info.values())
            ctx.wosg_summary = {"median_lowfreq_power_ratio": float(np.median(ratios)), "chosen_parameter_counts": dict(cnt)}
            save_json({"configuration": dict(cfg.wosg), "summary": ctx.wosg_summary,
                       "warnings": ["WOSG wavelet, level, SG parameters and optimisation criterion are NOT specified in the base paper; values here are assumptions.",
                                    "The per-recording (window, order) criterion is an unsupervised proxy of this project, not the published optimisation."]},
                      dirs["config"] / "wosg_parameters.json")
            LOG.info("WOSG applied to %d recordings; median low-frequency power reduction x%.1f; parameter choices %s",
                     len(ctx.filt), ctx.wosg_summary["median_lowfreq_power_ratio"], dict(cnt))
        with stage("4 Segmentation, GWST and 450-D features"):
            build_representation(ctx)
        with stage("5-6 Outer cross-validation (baselines, encoders, heads, fine-tuning, thresholds, noise)"):
            run_outer_cv(ctx)
        if cfg.run.run_loao:
            with stage("7 Leave-one-activity-out"):
                run_loao(ctx)
        with stage("8 Aggregation: metrics, bootstrap CI, paired comparisons"):
            R = aggregate_results(ctx)
            ctx.R = R
            save_json({"histories": ctx.histories}, dirs["metrics"] / "training_histories.json")
            for k, (vl, pth) in ctx.best_enc.items():
                if pth is not None:
                    shutil.copy(pth, dirs["checkpoints"] / ("%s_best.pt" % k))
                    LOG.info("Best %s encoder (lowest validation loss %.4f): %s", k, vl, pth.name)
        for nm, fn in (("9 Plots", lambda: (plot_signals(ctx), plot_gwst(ctx), plot_training_curves(ctx), plot_confusions(ctx, R["rec_fold"], R["win_clean"]),
                                            plot_roc(ctx, R["rec_fold"]), plot_activity(ctx, R.get("activity")), plot_holdout(ctx, R.get("loao_summary")),
                                            plot_noise(ctx, R.get("noise")), plot_noise_examples(ctx), plot_recording_level(ctx, R["rec_fold"]),
                                            plot_model_comparison(ctx, R["rec_tbl"]))),
                       ("10 Diagrams", lambda: (diagram_architecture(ctx), diagram_quantum_circuit(ctx), diagram_methodology(ctx), diagram_pipeline(ctx, PIPELINE_STAGES))),
                       ("11 Reports", lambda: (write_methodology_report(ctx, inv, selftests, grad),
                                               write_final_report(ctx, R, interpret(ctx, R)), write_base_paper_comparison(ctx, R)))):
            try:
                with stage(nm):
                    fn()
            except Exception:
                LOG.error("Non-critical stage '%s' failed (see traceback above); continuing.", nm)
        status = 0
    except Exception:
        LOG.error("PIPELINE ABORTED\n%s", traceback.format_exc())
        status = 1
    finally:
        if not args.keep_cache:
            with contextlib.suppress(Exception):
                if hasattr(ctx, "Smag"):
                    del ctx.Smag
                shutil.rmtree(dirs["cache"], ignore_errors=True)
        LOG.info("Total wall-clock time %.1f min. Outputs in %s", (time.time() - t_start) / 60, root)
        logging.shutdown()
    return status


if __name__ == "__main__":
    sys.exit(main())
