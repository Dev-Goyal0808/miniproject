# GWST + Quantum Classifier: Augmentation Ablation

Two independent pipeline executions used the same seed and five-fold recording-grouped split protocol.
The only intended difference is training-only MixUp: alpha=0.00 versus alpha=0.15.
Validation and test recordings are not augmented. The table below is extracted from the generated run metrics.

**Important:** MixUp is the augmentation tested here; this is not a test of Gaussian/EMG/ocular waveform augmentation.
The quick profile uses one seed and shortened training, so treat this as a final limited-scope ablation, not a multi-seed definitive estimate.

| Condition | Model | accuracy_mean | balanced_accuracy_mean | precision_mean | sensitivity_mean | specificity_mean | f1_mean | macro_f1_mean | roc_auc_mean | pr_auc_mean | mcc_mean | balanced_accuracy_std | accuracy_std |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| without_augmentation (alpha=0.0) | Transformer + RBF-SVM (matched classical head) | 0.8333 | 0.8250 | 0.7425 | 0.8000 | 0.8500 | 0.7548 | 0.8128 | 0.8861 | 0.8197 | 0.6470 | 0.1079 | 0.0878 |
| without_augmentation (alpha=0.0) | Transformer + 6-qubit VQC | 0.8222 | 0.7917 | 0.7443 | 0.7000 | 0.8833 | 0.7130 | 0.7917 | 0.8611 | 0.7909 | 0.5937 | 0.1141 | 0.0824 |
| without_augmentation (alpha=0.0) | Bi-LSTM + RBF-SVM (matched classical head) | 0.7667 | 0.7500 | 0.6600 | 0.7000 | 0.8000 | 0.6655 | 0.7417 | 0.9000 | 0.8472 | 0.5019 | 0.0589 | 0.0609 |
| without_augmentation (alpha=0.0) | Bi-LSTM + 6-qubit VQC | 0.7667 | 0.7583 | 0.6576 | 0.7333 | 0.7833 | 0.6735 | 0.7434 | 0.8722 | 0.7941 | 0.5183 | 0.0745 | 0.0724 |
| with_mixup_augmentation (alpha=0.15) | Transformer + RBF-SVM (matched classical head) | 0.8333 | 0.8250 | 0.7425 | 0.8000 | 0.8500 | 0.7548 | 0.8128 | 0.8861 | 0.8197 | 0.6470 | 0.1079 | 0.0878 |
| with_mixup_augmentation (alpha=0.15) | Transformer + 6-qubit VQC | 0.8222 | 0.7917 | 0.7443 | 0.7000 | 0.8833 | 0.7130 | 0.7917 | 0.8611 | 0.7909 | 0.5937 | 0.1141 | 0.0824 |
| with_mixup_augmentation (alpha=0.15) | Bi-LSTM + RBF-SVM (matched classical head) | 0.7667 | 0.7500 | 0.6600 | 0.7000 | 0.8000 | 0.6655 | 0.7417 | 0.9000 | 0.8472 | 0.5019 | 0.0589 | 0.0609 |
| with_mixup_augmentation (alpha=0.15) | Bi-LSTM + 6-qubit VQC | 0.7667 | 0.7583 | 0.6576 | 0.7333 | 0.7833 | 0.6735 | 0.7434 | 0.8722 | 0.7941 | 0.5183 | 0.0745 | 0.0724 |

## Run provenance

- Pipeline script: `C:\Users\devgo\OneDrive\Desktop\mini project\hybrid_quantum_eeg_epilepsy.py`
- Seed: `0`; folds: `5`; profile: `quick`; device requested: `auto`
- No fine-tuning, leave-one-activity-out, or synthetic-noise evaluation was run.
- Machine-readable comparison: `C:\Users\devgo\OneDrive\Desktop\mini project\outputs_gwst_vqc_ablation\gwst_vqc_augmentation_comparison.csv`
