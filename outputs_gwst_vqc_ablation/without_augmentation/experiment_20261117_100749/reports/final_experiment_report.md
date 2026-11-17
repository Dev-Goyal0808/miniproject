# Final experiment report

> Auto-generated from the numbers produced in this run. Nothing in this report is hard-coded or taken from the base paper. Profile: **quick**, seeds [0], 5 outer folds.

## 1. What was run

- Dataset: 90 recordings (60 healthy / 30 epilepsy), 360 windows of 5 s (non-overlapping).
- Evaluation unit: **recording** (mean of window probabilities, validation-selected threshold). Window-level metrics are secondary.
- Splits: grouped by recording (no participant IDs exist -> **no participant-independent claim**).
- Experiments: E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12T, E12B.

## 2. Primary results - recording level, frozen encoders and classical baselines

Pooled over all outer test folds, averaged over 1 seed(s); CI = 95% bootstrap over recordings. All models share identical folds, partitions and (for E4-E12) identical 6-D embeddings.

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.775 [0.692, 0.858] | 0.822 [0.739, 0.900] | 0.633 | 0.917 | 0.871 | 0.586 | 0.717 |
| E2 | GWST-450 + SVM | 0.783 [0.678, 0.870] | 0.822 [0.722, 0.889] | 0.667 | 0.900 | 0.896 | 0.589 | 0.717 |
| E3 | GWST-450 + MI selection + Random Forest | 0.708 [0.611, 0.808] | 0.744 [0.661, 0.822] | 0.600 | 0.817 | 0.821 | 0.420 | 0.671 |
| E4 | Transformer + 6-D embedding + linear | 0.825 [0.738, 0.904] | 0.844 [0.772, 0.922] | 0.767 | 0.883 | 0.883 | 0.650 | 0.756 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.825 [0.745, 0.906] | 0.844 [0.778, 0.922] | 0.767 | 0.883 | 0.877 | 0.650 | 0.762 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.825 [0.730, 0.914] | 0.833 [0.756, 0.906] | 0.800 | 0.850 | 0.902 | 0.636 | 0.758 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.792 [0.700, 0.877] | 0.822 [0.750, 0.895] | 0.700 | 0.883 | 0.854 | 0.594 | 0.746 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.817 [0.743, 0.890] | 0.822 [0.756, 0.889] | 0.800 | 0.833 | 0.889 | 0.616 | 0.756 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.825 [0.746, 0.897] | 0.822 [0.744, 0.900] | 0.833 | 0.817 | 0.890 | 0.625 | 0.762 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.750 [0.646, 0.835] | 0.767 [0.678, 0.844] | 0.700 | 0.800 | 0.887 | 0.489 | 0.758 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.758 [0.662, 0.849] | 0.767 [0.678, 0.856] | 0.733 | 0.783 | 0.862 | 0.500 | 0.756 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.792 [0.711, 0.876] | 0.811 [0.733, 0.889] | 0.733 | 0.850 | 0.813 | 0.579 | 0.767 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.825 [0.743, 0.910] | 0.844 [0.767, 0.911] | 0.767 | 0.883 | 0.849 | 0.650 | 0.756 |

Fold-wise mean ± sd (n = seeds x folds; NaN-aware):

| ID | Model | folds evaluated | Bal. acc. (mean ± sd over folds) | Accuracy (mean ± sd) | Macro-F1 | ROC-AUC (valid folds) | ROC-AUC n valid |
|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 5 | 0.775 ± 0.096 | 0.822 ± 0.061 | 0.781 | 0.886 | 5 |
| E2 | GWST-450 + SVM | 5 | 0.783 ± 0.062 | 0.822 ± 0.046 | 0.791 | 0.906 | 5 |
| E3 | GWST-450 + MI selection + Random Forest | 5 | 0.708 ± 0.102 | 0.744 ± 0.108 | 0.707 | 0.833 | 5 |
| E4 | Transformer + 6-D embedding + linear | 5 | 0.825 ± 0.108 | 0.844 ± 0.072 | 0.820 | 0.886 | 5 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 5 | 0.825 ± 0.090 | 0.844 ± 0.082 | 0.825 | 0.881 | 5 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 5 | 0.825 ± 0.108 | 0.833 ± 0.088 | 0.813 | 0.886 | 5 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 5 | 0.792 ± 0.114 | 0.822 ± 0.082 | 0.792 | 0.861 | 5 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 5 | 0.792 ± 0.118 | 0.811 ± 0.108 | 0.788 | 0.836 | 5 |
| E8 | Bi-LSTM + 6-D embedding + linear | 5 | 0.817 ± 0.056 | 0.822 ± 0.046 | 0.805 | 0.903 | 5 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 5 | 0.825 ± 0.075 | 0.822 ± 0.072 | 0.809 | 0.897 | 5 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 5 | 0.750 ± 0.059 | 0.767 ± 0.061 | 0.742 | 0.900 | 5 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 5 | 0.758 ± 0.075 | 0.767 ± 0.072 | 0.743 | 0.872 | 5 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 5 | 0.825 ± 0.054 | 0.844 ± 0.046 | 0.825 | 0.864 | 5 |

## 3. End-to-end fine-tuned models (separate comparison - not comparable 1:1 with Section 2)

_not run in this profile_


## 4. Primary results restricted to activities present in both classes

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.774 [0.672, 0.859] | 0.805 [0.701, 0.883] | 0.633 | 0.915 | 0.879 | 0.584 | 0.727 |
| E2 | GWST-450 + SVM | 0.780 [0.690, 0.879] | 0.805 [0.714, 0.890] | 0.667 | 0.894 | 0.884 | 0.584 | 0.711 |
| E3 | GWST-450 + MI selection + Random Forest | 0.704 [0.595, 0.802] | 0.727 [0.617, 0.818] | 0.600 | 0.809 | 0.821 | 0.417 | 0.675 |
| E4 | Transformer + 6-D embedding + linear | 0.820 [0.728, 0.899] | 0.831 [0.746, 0.909] | 0.767 | 0.872 | 0.867 | 0.643 | 0.727 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.820 [0.720, 0.903] | 0.831 [0.753, 0.909] | 0.767 | 0.872 | 0.862 | 0.643 | 0.735 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.804 [0.707, 0.889] | 0.805 [0.714, 0.883] | 0.800 | 0.809 | 0.881 | 0.600 | 0.738 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.776 [0.683, 0.870] | 0.792 [0.701, 0.870] | 0.700 | 0.851 | 0.835 | 0.559 | 0.731 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.794 [0.699, 0.872] | 0.792 [0.701, 0.864] | 0.800 | 0.787 | 0.867 | 0.577 | 0.733 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.800 [0.701, 0.879] | 0.792 [0.694, 0.870] | 0.833 | 0.766 | 0.867 | 0.586 | 0.742 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.722 [0.610, 0.814] | 0.727 [0.623, 0.818] | 0.700 | 0.745 | 0.862 | 0.438 | 0.735 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.739 [0.628, 0.837] | 0.740 [0.636, 0.831] | 0.733 | 0.745 | 0.843 | 0.469 | 0.742 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.782 [0.681, 0.875] | 0.792 [0.701, 0.883] | 0.733 | 0.830 | 0.798 | 0.563 | 0.747 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.809 [0.718, 0.898] | 0.818 [0.727, 0.896] | 0.767 | 0.851 | 0.829 | 0.618 | 0.738 |


## 5. Matched classical-vs-quantum comparison (same embeddings)

Difference = model_a - model_b in recording-level metric; CI from paired bootstrap over recordings; McNemar exact p per seed (uncorrected, exploratory).

| model_a | model_b | mean_difference_a_minus_b | ci_low | ci_high | ci_excludes_zero | mcnemar_a_only_correct | mcnemar_b_only_correct | mcnemar_exact_p_per_seed |
|---|---|---|---|---|---|---|---|---|
| E7 | E4 | -0.033 | -0.115 | 0.039 | False | 4.000 | 6.000 | 0.754 |
| E7 | E5 | -0.033 | -0.118 | 0.050 | False | 5.000 | 7.000 | 0.774 |
| E7 | E6 | -0.033 | -0.104 | 0.043 | False | 3.000 | 4.000 | 1.000 |
| E7 | E12T | 0.000 | -0.071 | 0.081 | False | 7.000 | 6.000 | 1.000 |
| E11 | E8 | -0.058 | -0.122 | -0.005 | True | 2.000 | 7.000 | 0.180 |
| E11 | E9 | -0.067 | -0.127 | -0.008 | True | 2.000 | 7.000 | 0.180 |
| E11 | E10 | 0.008 | -0.059 | 0.077 | False | 6.000 | 6.000 | 1.000 |
| E11 | E12B | -0.067 | -0.150 | 0.024 | False | 3.000 | 10.000 | 0.092 |
| E4 | E8 | 0.008 | -0.065 | 0.077 | False | 6.000 | 4.000 | 0.754 |
| E5 | E9 | 0.000 | -0.066 | 0.062 | False | 6.000 | 4.000 | 0.754 |
| E6 | E10 | 0.075 | -0.012 | 0.170 | False | 8.000 | 2.000 | 0.109 |
| E7 | E11 | 0.033 | -0.045 | 0.112 | False | 9.000 | 4.000 | 0.267 |
| E1 | E2 | -0.008 | -0.097 | 0.083 | False | 6.000 | 6.000 | 1.000 |
| E1 | E3 | 0.067 | 0.000 | 0.144 | False | 10.000 | 3.000 | 0.092 |


## 6. Activity-wise and activity-group results (recording-level accuracy; pooled outer-CV test predictions)

Per-activity sample sizes are tiny (2-10 recordings per class); treat as descriptive. Healthy-only activities can only yield accuracy = specificity.

| unit | E1 | E11 | E2 | E5 | E7 | E9 |
|---|---|---|---|---|---|---|
| cooking | 0.667 | 0.667 | 0.667 | 0.667 | 1.000 | 1.000 |
| desk work | 0.800 | 0.600 | 0.700 | 0.700 | 0.800 | 0.700 |
| idle sitting | 0.714 | 0.571 | 0.714 | 0.714 | 0.571 | 0.571 |
| intense_ambulatory | 0.765 | 0.824 | 0.765 | 0.882 | 0.765 | 0.824 |
| jogging | 0.889 | 0.889 | 0.889 | 1.000 | 0.889 | 0.889 |
| jumping | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| laying | 0.400 | 0.400 | 0.400 | 0.600 | 0.800 | 0.600 |
| light_ambulatory | 0.964 | 0.893 | 0.964 | 0.929 | 0.964 | 0.929 |
| running | 0.625 | 0.750 | 0.625 | 0.750 | 0.625 | 0.750 |
| sitting | 0.700 | 0.600 | 0.800 | 0.800 | 0.500 | 0.700 |
| stairs | 1.000 | 0.833 | 0.917 | 0.917 | 0.917 | 0.833 |
| standing | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| stationary | 0.688 | 0.562 | 0.688 | 0.719 | 0.656 | 0.656 |
| walking | 0.938 | 0.938 | 1.000 | 0.938 | 1.000 | 1.000 |
| watching tv | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |


## 9. Training cost

| model | params | seconds | epochs |
|---|---|---|---|
| E1 | n/a | 1.6 | n/a |
| E10 | n/a | 0.1 | n/a |
| E11 | 31.0 | 7.9 | 26.8 |
| E12B | 31.0 | 8.5 | 33.4 |
| E12T | 31.0 | 9.3 | 35.6 |
| E2 | n/a | 1.0 | n/a |
| E3 | n/a | 7.4 | n/a |
| E4 | 7.0 | 0.1 | 10.6 |
| E5 | 49.0 | 0.1 | 9.8 |
| E6 | n/a | 0.1 | n/a |
| E7 | 31.0 | 11.0 | 35.8 |
| E8 | 7.0 | 0.1 | 16.0 |
| E9 | 49.0 | 0.1 | 12.8 |
| pretrain_bilstm | 14982.0 | 1.2 | 17.6 |
| pretrain_transformer | 25734.0 | 2.6 | 17.6 |


## 10. Interpretation (data-driven; see also results_interpretation.md)

- Highest pooled recording-level balanced accuracy among frozen/classical models: **E4 (T+Linear)** = 0.825 [0.738, 0.904]. Differences between nearby models are usually within the bootstrap CIs (n = 90 recordings), so this ranking is not a statistically established order.
- Transformer head, VQC (E7) minus E4 (T+Linear), recording-level balanced accuracy: -0.033 [-0.115, +0.039] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E5 (T+MLP), recording-level balanced accuracy: -0.033 [-0.118, +0.050] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E6 (T+RBF-SVM), recording-level balanced accuracy: -0.033 [-0.104, +0.043] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E12T (T+VQC(noCNOT)), recording-level balanced accuracy: +0.000 [-0.071, +0.081] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E11 (B+VQC), recording-level balanced accuracy: +0.033 [-0.045, +0.112] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E8 (B+Linear), recording-level balanced accuracy: -0.058 [-0.122, -0.005] -> VQC lower and the CI excludes 0.
- Bi-LSTM head, VQC (E11) minus E9 (B+MLP), recording-level balanced accuracy: -0.067 [-0.127, -0.008] -> VQC lower and the CI excludes 0.
- Bi-LSTM head, VQC (E11) minus E10 (B+RBF-SVM), recording-level balanced accuracy: +0.008 [-0.059, +0.077] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E12B (B+VQC(noCNOT)), recording-level balanced accuracy: -0.067 [-0.150, +0.024] -> no distinguishable difference (CI includes 0).
- Cost: VQC head trainable parameters = 31.0 vs MLP head = 49.0; mean head fitting time 11.0 s (VQC, classical simulation) vs 0.1 s (MLP). Simulation overhead is not evidence about quantum hardware.
- The 6-D embedding for the frozen comparison was pre-trained with a linear head; heads of that type may be favoured.
- **Quantum-advantage statement:** this study simulates a 6-qubit circuit on a classical machine and compares it with matched classical heads on one small dataset. No paired comparison shows the VQC to be better than a matched classical head with a CI excluding 0. In no case is quantum advantage or supremacy claimed.

## 11. Limitations

- 90 recordings (30 epilepsy); folds contain ~6 epilepsy recordings, so every estimate has wide uncertainty.
- No participant IDs: recording-level grouping cannot exclude person-level leakage; results are **not** participant-independent.
- Healthy-only activities (standing, TV, cooking, jumping) can act as shortcuts in the main CV; see the paired-activities-only table.
- WOSG parameters/criterion and the exact GWST implementation details of the base paper are not published; assumptions are listed in the methodology report.
- Quantum models are classically simulated; no hardware, noise or shot-noise effects are evaluated.
- Fixed learning rates for neural models; only sklearn models are grid-tuned.
- Synthetic corruptions are not real artefacts.

## 12. Output index

`config/` configuration, environment, audit, folds; `data/` features and predictions; `metrics/` all CSV tables; `plots/`; `diagrams/`; `checkpoints/`; `logs/`.
