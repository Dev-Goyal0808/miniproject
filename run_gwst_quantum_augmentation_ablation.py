#!/usr/bin/env python3
"""Run one paired GWST + VQC ablation: no MixUp vs training-only MixUp.

Place this file beside hybrid_quantum_eeg_epilepsy.py (or
hybrid_quantum_eeg_epilepsy_enhanced.py), then run:
    python run_gwst_quantum_augmentation_ablation.py --data-path "ADLs using a Portable EEG Headset.zip"

It launches the existing, audited pipeline twice with the SAME quick-profile
seed and grouped five-fold protocol. Only train-fold MixUp differs:
    condition A: mixup_alpha = 0.00 (no MixUp)
    condition B: mixup_alpha = 0.15 (training-only MixUp)

The pipeline still computes the full model catalogue; this wrapper extracts
GWST + Transformer/Bi-LSTM + VQC (E7/E11), and matched RBF-SVM heads (E6/E10)
for context. All reported metrics are read from the generated CSV files.
No results are pre-filled or fabricated.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
import pandas as pd


def find_pipeline(folder: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Pipeline script not found: {p}")
        return p
    candidates = [folder / "hybrid_quantum_eeg_epilepsy.py",
                  folder / "hybrid_quantum_eeg_epilepsy_enhanced.py",
                  folder / "gwst_quantum_aug_ablation.py"]
    for p in candidates:
        if p.is_file() and p.resolve() != Path(__file__).resolve():
            return p.resolve()
    raise FileNotFoundError("Put the original hybrid_quantum_eeg_epilepsy.py (or *_enhanced.py) beside this script, or pass --pipeline.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Paired GWST-VQC MixUp ablation")
    ap.add_argument("--data-path", default=None, help="Dataset ZIP or extracted CSV directory")
    ap.add_argument("--pipeline", default=None, help="Path to the existing full pipeline script")
    ap.add_argument("--output-root", default="outputs_gwst_vqc_ablation")
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    pipeline = find_pipeline(here, args.pipeline)
    out_root = Path(args.output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    config_dir = out_root / "configs"
    config_dir.mkdir(exist_ok=True)

    runs = []
    for label, alpha in (("without_augmentation", 0.0), ("with_mixup_augmentation", 0.15)):
        cfg_path = config_dir / f"{label}.json"
        cfg_path.write_text(json.dumps({"train": {"mixup_alpha": alpha}}, indent=2), encoding="utf-8")
        cmd = [sys.executable, str(pipeline), "--profile", "quick",
               "--output-root", str(out_root / label), "--seeds", str(args.seed),
               "--n-folds", "5", "--device", args.device,
               "--no-finetune", "--no-loao", "--no-noise", "--config-json", str(cfg_path)]
        if args.data_path:
            cmd += ["--data-path", args.data_path]
        print("\n" + "=" * 76)
        print(f"RUN: {label} | mixup_alpha={alpha}")
        print("COMMAND:", subprocess.list2cmdline(cmd))
        started = time.time()
        completed = subprocess.run(cmd, cwd=str(pipeline.parent))
        print(f"Finished with exit code {completed.returncode} in {(time.time()-started)/60:.1f} min")
        if completed.returncode != 0:
            print("Run failed. Check the run's logs folder; no comparison report was generated.")
            return completed.returncode

        # The underlying pipeline creates the newest experiment folder under this run root.
        run_base = out_root / label
        exp_dirs = sorted(run_base.glob("experiment_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not exp_dirs:
            raise FileNotFoundError(f"No experiment output folder found under {run_base}")
        exp_dir = exp_dirs[0]
        metrics_file = exp_dir / "metrics" / "summary_metrics.csv"
        if not metrics_file.is_file():
            raise FileNotFoundError(f"Expected metrics file missing: {metrics_file}")
        df = pd.read_csv(metrics_file)
        # The primary table is recording-level fold metrics. Retain only VQC and
        # matched classical RBF-SVM heads for the requested focused comparison.
        if "level" in df.columns:
            df = df[df.level.astype(str).str.lower().eq("recording")]
        keep = ["E7", "E11", "E6", "E10"]
        df = df[df.model.isin(keep)].copy()
        df.insert(0, "augmentation", label)
        df["mixup_alpha"] = alpha
        df["experiment_directory"] = str(exp_dir)
        runs.append(df)
        print("Metrics loaded:", metrics_file)

    if not runs or any(d.empty for d in runs):
        raise RuntimeError("One or both runs did not contain the expected E6/E7/E10/E11 recording-level metrics.")
    combined = pd.concat(runs, ignore_index=True)
    metrics_out = out_root / "gwst_vqc_augmentation_comparison.csv"
    combined.to_csv(metrics_out, index=False)

    names = {"E6": "Transformer + RBF-SVM (matched classical head)",
             "E7": "Transformer + 6-qubit VQC",
             "E10": "Bi-LSTM + RBF-SVM (matched classical head)",
             "E11": "Bi-LSTM + 6-qubit VQC"}
    metric_cols = [c for c in ["accuracy_mean", "balanced_accuracy_mean", "precision_mean",
                               "sensitivity_mean", "specificity_mean", "f1_mean", "macro_f1_mean",
                               "roc_auc_mean", "pr_auc_mean", "mcc_mean",
                               "balanced_accuracy_std", "accuracy_std"] if c in combined.columns]
    lines = ["# GWST + Quantum Classifier: Augmentation Ablation", "",
             "Two independent pipeline executions used the same seed and five-fold recording-grouped split protocol.",
             "The only intended difference is training-only MixUp: alpha=0.00 versus alpha=0.15.",
             "Validation and test recordings are not augmented. The table below is extracted from the generated run metrics.", "",
             "**Important:** MixUp is the augmentation tested here; this is not a test of Gaussian/EMG/ocular waveform augmentation.",
             "The quick profile uses one seed and shortened training, so treat this as a final limited-scope ablation, not a multi-seed definitive estimate.", "",
             "| Condition | Model | " + " | ".join(metric_cols) + " |",
             "|---|---|" + "|".join(["---:"] * len(metric_cols)) + "|"]
    for _, row in combined.iterrows():
        vals = []
        for col in metric_cols:
            v = row.get(col)
            vals.append("NA" if pd.isna(v) else f"{float(v):.4f}")
        lines.append("| %s (alpha=%s) | %s | %s |" % (row.augmentation, row.mixup_alpha,
                      names.get(row.model, row.model), " | ".join(vals)))
    lines += ["", "## Run provenance", "",
              f"- Pipeline script: `{pipeline}`",
              f"- Seed: `{args.seed}`; folds: `5`; profile: `quick`; device requested: `{args.device}`",
              f"- No fine-tuning, leave-one-activity-out, or synthetic-noise evaluation was run.",
              f"- Machine-readable comparison: `{metrics_out}`", ""]
    report = out_root / "gwst_vqc_augmentation_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\nCompleted paired ablation.")
    print("CSV:", metrics_out)
    print("Report:", report)
    print("Actual experiment folders:")
    for d in combined.experiment_directory.drop_duplicates():
        print(" -", d)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
