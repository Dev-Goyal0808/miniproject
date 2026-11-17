# Final experiment report

> Auto-generated from the numbers produced in this run. Nothing in this report is hard-coded or taken from the base paper. Profile: **full**, seeds [0, 1, 2], 5 outer folds.

## 1. What was run

- Dataset: 90 recordings (60 healthy / 30 epilepsy), 360 windows of 5 s (non-overlapping).
- Evaluation unit: **recording** (mean of window probabilities, validation-selected threshold). Window-level metrics are secondary.
- Splits: grouped by recording (no participant IDs exist -> **no participant-independent claim**).
- Experiments: E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12T, E12B, FT-T-lin, FT-T-mlp, FT-T-vqc, FT-B-lin, FT-B-mlp, FT-B-vqc.

## 2. Primary results - recording level, frozen encoders and classical baselines

Pooled over all outer test folds, averaged over 3 seed(s); CI = 95% bootstrap over recordings. All models share identical folds, partitions and (for E4-E12) identical 6-D embeddings.

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.742 [0.664, 0.817] | 0.796 [0.722, 0.859] | 0.578 | 0.906 | 0.873 | 0.527 | 0.722 |
| E2 | GWST-450 + SVM | 0.767 [0.691, 0.839] | 0.811 [0.741, 0.870] | 0.633 | 0.900 | 0.889 | 0.562 | 0.718 |
| E3 | GWST-450 + MI selection + Random Forest | 0.700 [0.625, 0.780] | 0.730 [0.659, 0.800] | 0.611 | 0.789 | 0.808 | 0.401 | 0.685 |
| E4 | Transformer + 6-D embedding + linear | 0.811 [0.743, 0.882] | 0.819 [0.755, 0.882] | 0.789 | 0.833 | 0.891 | 0.613 | 0.756 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.814 [0.745, 0.884] | 0.833 [0.767, 0.896] | 0.756 | 0.872 | 0.894 | 0.627 | 0.765 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.797 [0.720, 0.867] | 0.815 [0.748, 0.881] | 0.744 | 0.850 | 0.899 | 0.590 | 0.758 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.761 [0.686, 0.832] | 0.774 [0.707, 0.837] | 0.722 | 0.800 | 0.825 | 0.509 | 0.753 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.811 [0.737, 0.875] | 0.819 [0.755, 0.878] | 0.789 | 0.833 | 0.876 | 0.609 | 0.751 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.792 [0.718, 0.860] | 0.804 [0.737, 0.867] | 0.756 | 0.828 | 0.875 | 0.572 | 0.755 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.781 [0.707, 0.852] | 0.804 [0.737, 0.867] | 0.711 | 0.850 | 0.882 | 0.560 | 0.756 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.747 [0.673, 0.819] | 0.759 [0.689, 0.826] | 0.711 | 0.783 | 0.831 | 0.485 | 0.728 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.767 [0.698, 0.833] | 0.767 [0.700, 0.833] | 0.767 | 0.767 | 0.791 | 0.515 | 0.759 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.753 [0.679, 0.821] | 0.763 [0.696, 0.826] | 0.722 | 0.783 | 0.783 | 0.493 | 0.741 |

Fold-wise mean ± sd (n = seeds x folds; NaN-aware):

| ID | Model | folds evaluated | Bal. acc. (mean ± sd over folds) | Accuracy (mean ± sd) | Macro-F1 | ROC-AUC (valid folds) | ROC-AUC n valid |
|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 15 | 0.742 ± 0.073 | 0.796 ± 0.054 | 0.748 | 0.895 | 15 |
| E2 | GWST-450 + SVM | 15 | 0.767 ± 0.097 | 0.811 ± 0.091 | 0.769 | 0.897 | 15 |
| E3 | GWST-450 + MI selection + Random Forest | 15 | 0.700 ± 0.110 | 0.730 ± 0.107 | 0.685 | 0.815 | 15 |
| E4 | Transformer + 6-D embedding + linear | 15 | 0.811 ± 0.097 | 0.819 ± 0.090 | 0.800 | 0.891 | 15 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 15 | 0.814 ± 0.085 | 0.833 ± 0.073 | 0.810 | 0.894 | 15 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 15 | 0.797 ± 0.079 | 0.815 ± 0.078 | 0.792 | 0.891 | 15 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 15 | 0.761 ± 0.111 | 0.774 ± 0.102 | 0.750 | 0.827 | 15 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 15 | 0.767 ± 0.101 | 0.767 ± 0.090 | 0.747 | 0.794 | 15 |
| E8 | Bi-LSTM + 6-D embedding + linear | 15 | 0.811 ± 0.083 | 0.819 ± 0.083 | 0.800 | 0.885 | 15 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 15 | 0.792 ± 0.074 | 0.804 ± 0.072 | 0.783 | 0.881 | 15 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 15 | 0.781 ± 0.078 | 0.804 ± 0.069 | 0.774 | 0.892 | 15 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 15 | 0.747 ± 0.085 | 0.759 ± 0.102 | 0.736 | 0.844 | 15 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 15 | 0.753 ± 0.111 | 0.763 ± 0.106 | 0.738 | 0.782 | 15 |

## 3. End-to-end fine-tuned models (separate comparison - not comparable 1:1 with Section 2)

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| FT-T-lin | [fine-tuned] Transformer + linear | 0.794 [0.728, 0.861] | 0.796 [0.730, 0.859] | 0.789 | 0.800 | 0.902 | 0.571 | 0.772 |
| FT-T-mlp | [fine-tuned] Transformer + MLP | 0.808 [0.739, 0.878] | 0.807 [0.741, 0.870] | 0.811 | 0.806 | 0.888 | 0.594 | 0.758 |
| FT-T-vqc | [fine-tuned] Transformer + VQC | 0.789 [0.710, 0.867] | 0.819 [0.748, 0.882] | 0.700 | 0.878 | 0.880 | 0.588 | 0.760 |
| FT-B-lin | [fine-tuned] Bi-LSTM + linear | 0.775 [0.700, 0.851] | 0.793 [0.726, 0.863] | 0.722 | 0.828 | 0.884 | 0.542 | 0.751 |
| FT-B-mlp | [fine-tuned] Bi-LSTM + MLP | 0.764 [0.685, 0.846] | 0.774 [0.696, 0.848] | 0.733 | 0.794 | 0.879 | 0.512 | 0.756 |
| FT-B-vqc | [fine-tuned] Bi-LSTM + VQC | 0.789 [0.711, 0.860] | 0.807 [0.737, 0.870] | 0.733 | 0.844 | 0.862 | 0.571 | 0.726 |


## 4. Primary results restricted to activities present in both classes

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.739 [0.653, 0.813] | 0.775 [0.693, 0.853] | 0.578 | 0.901 | 0.873 | 0.522 | 0.723 |
| E2 | GWST-450 + SVM | 0.763 [0.684, 0.842] | 0.792 [0.710, 0.866] | 0.633 | 0.894 | 0.873 | 0.554 | 0.706 |
| E3 | GWST-450 + MI selection + Random Forest | 0.692 [0.608, 0.774] | 0.710 [0.628, 0.788] | 0.611 | 0.773 | 0.807 | 0.389 | 0.683 |
| E4 | Transformer + 6-D embedding + linear | 0.802 [0.723, 0.875] | 0.805 [0.732, 0.874] | 0.789 | 0.816 | 0.874 | 0.602 | 0.731 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.800 [0.717, 0.874] | 0.810 [0.732, 0.879] | 0.756 | 0.844 | 0.876 | 0.600 | 0.746 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.776 [0.696, 0.852] | 0.784 [0.710, 0.857] | 0.744 | 0.809 | 0.877 | 0.551 | 0.739 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.744 [0.665, 0.818] | 0.749 [0.675, 0.818] | 0.722 | 0.766 | 0.807 | 0.483 | 0.737 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.795 [0.719, 0.871] | 0.797 [0.723, 0.870] | 0.789 | 0.801 | 0.856 | 0.585 | 0.731 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.775 [0.701, 0.849] | 0.779 [0.706, 0.853] | 0.756 | 0.794 | 0.855 | 0.544 | 0.736 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.763 [0.687, 0.837] | 0.775 [0.701, 0.844] | 0.711 | 0.816 | 0.859 | 0.528 | 0.738 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.724 [0.649, 0.797] | 0.727 [0.654, 0.801] | 0.711 | 0.738 | 0.808 | 0.447 | 0.710 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.745 [0.670, 0.818] | 0.740 [0.662, 0.814] | 0.767 | 0.723 | 0.763 | 0.484 | 0.742 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.744 [0.668, 0.822] | 0.749 [0.671, 0.823] | 0.722 | 0.766 | 0.771 | 0.485 | 0.726 |


## 5. Matched classical-vs-quantum comparison (same embeddings)

Difference = model_a - model_b in recording-level metric; CI from paired bootstrap over recordings; McNemar exact p per seed (uncorrected, exploratory).

| model_a | model_b | mean_difference_a_minus_b | ci_low | ci_high | ci_excludes_zero | mcnemar_a_only_correct | mcnemar_b_only_correct | mcnemar_exact_p_per_seed |
|---|---|---|---|---|---|---|---|---|
| E7 | E4 | -0.050 | -0.103 | 0.002 | False | 15.000 | 27.000 | 0.180;0.302;0.003 |
| E7 | E5 | -0.053 | -0.095 | -0.007 | True | 13.000 | 29.000 | 0.092;1.000;0.013 |
| E7 | E6 | -0.036 | -0.085 | 0.008 | False | 8.000 | 19.000 | 0.070;1.000;0.388 |
| E7 | E12T | -0.006 | -0.045 | 0.033 | False | 23.000 | 21.000 | 0.804;0.774;0.804 |
| E11 | E8 | -0.064 | -0.117 | -0.010 | True | 11.000 | 27.000 | 0.210;1.000;0.012 |
| E11 | E9 | -0.044 | -0.091 | 0.004 | False | 13.000 | 25.000 | 0.210;0.754;0.039 |
| E11 | E10 | -0.033 | -0.078 | 0.015 | False | 14.000 | 26.000 | 0.774;1.000;0.035 |
| E11 | E12B | -0.006 | -0.053 | 0.034 | False | 14.000 | 15.000 | 0.549;0.508;1.000 |
| E4 | E8 | 0.000 | -0.061 | 0.069 | False | 24.000 | 24.000 | 1.000;0.167;0.143 |
| E5 | E9 | 0.022 | -0.040 | 0.087 | False | 28.000 | 20.000 | 1.000;1.000;0.143 |
| E6 | E10 | 0.017 | -0.047 | 0.086 | False | 22.000 | 19.000 | 0.289;1.000;1.000 |
| E7 | E11 | 0.014 | -0.035 | 0.062 | False | 27.000 | 23.000 | 1.000;1.000;0.424 |
| E1 | E2 | -0.025 | -0.087 | 0.041 | False | 21.000 | 25.000 | 1.000;0.648;0.118 |
| E1 | E3 | 0.042 | -0.012 | 0.096 | False | 32.000 | 14.000 | 0.092;0.077;0.629 |
| FT-T-vqc | FT-T-lin | -0.006 | -0.050 | 0.042 | False | 22.000 | 16.000 | 0.508;1.000;0.424 |
| FT-T-vqc | FT-T-mlp | -0.019 | -0.069 | 0.026 | False | 19.000 | 16.000 | 0.508;1.000;1.000 |
| FT-B-vqc | FT-B-lin | 0.014 | -0.044 | 0.070 | False | 20.000 | 16.000 | 0.581;0.267;0.344 |
| FT-B-vqc | FT-B-mlp | 0.025 | -0.038 | 0.087 | False | 23.000 | 14.000 | 0.344;0.210;1.000 |


## 6. Activity-wise and activity-group results (recording-level accuracy; pooled outer-CV test predictions)

Per-activity sample sizes are tiny (2-10 recordings per class); treat as descriptive. Healthy-only activities can only yield accuracy = specificity.

| unit | E1 | E11 | E2 | E5 | E7 | E9 |
|---|---|---|---|---|---|---|
| cooking | 0.667 | 0.889 | 0.889 | 0.889 | 0.889 | 0.889 |
| desk work | 0.867 | 0.667 | 0.833 | 0.733 | 0.733 | 0.700 |
| idle sitting | 0.667 | 0.571 | 0.714 | 0.714 | 0.619 | 0.429 |
| intense_ambulatory | 0.706 | 0.784 | 0.784 | 0.843 | 0.784 | 0.843 |
| jogging | 0.741 | 0.852 | 0.926 | 0.889 | 0.889 | 0.926 |
| jumping | 1.000 | 1.000 | 0.933 | 1.000 | 0.933 | 1.000 |
| laying | 0.333 | 0.467 | 0.400 | 0.400 | 0.467 | 0.667 |
| light_ambulatory | 0.905 | 0.869 | 0.881 | 0.917 | 0.845 | 0.917 |
| running | 0.667 | 0.708 | 0.625 | 0.792 | 0.667 | 0.750 |
| sitting | 0.733 | 0.533 | 0.767 | 0.800 | 0.667 | 0.667 |
| stairs | 0.917 | 0.778 | 0.833 | 0.861 | 0.722 | 0.806 |
| standing | 1.000 | 0.833 | 0.833 | 1.000 | 0.833 | 0.833 |
| stationary | 0.698 | 0.573 | 0.719 | 0.698 | 0.646 | 0.625 |
| walking | 0.896 | 0.938 | 0.917 | 0.958 | 0.938 | 1.000 |
| watching tv | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |


## 7. Leave-one-activity-out (recording-level balanced accuracy)

Train on the other eligible activities, test on the held-out activity (complete recordings; validation partition drawn from training activities only).

| heldout | E1 | E10 | E11 | E12B | E12T | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| desk work | 0.571 | 0.595 | 0.651 | 0.786 | 0.698 | 0.563 | 0.659 | 0.762 | 0.762 | 0.810 | 0.690 | 0.619 | 0.579 |
| idle sitting | 0.542 | 0.500 | 0.431 | 0.375 | 0.500 | 0.556 | 0.542 | 0.500 | 0.500 | 0.500 | 0.458 | 0.500 | 0.500 |
| jogging | 0.417 | 0.722 | 0.833 | 0.750 | 0.889 | 0.528 | 0.417 | 0.806 | 0.778 | 0.861 | 0.778 | 0.806 | 0.806 |
| laying | 0.250 | 0.472 | 0.583 | 0.528 | 0.500 | 0.389 | 0.250 | 0.500 | 0.500 | 0.500 | 0.500 | 0.611 | 0.528 |
| running | 0.444 | 0.567 | 0.556 | 0.522 | 0.467 | 0.533 | 0.422 | 0.511 | 0.622 | 0.511 | 0.456 | 0.567 | 0.567 |
| sitting | 0.556 | 0.437 | 0.333 | 0.381 | 0.524 | 0.484 | 0.579 | 0.381 | 0.381 | 0.405 | 0.437 | 0.310 | 0.357 |
| stairs | 0.611 | 0.750 | 0.806 | 0.694 | 0.694 | 0.806 | 0.639 | 0.750 | 0.722 | 0.778 | 0.694 | 0.778 | 0.806 |
| walking | 0.717 | 0.883 | 0.900 | 0.917 | 0.706 | 0.917 | 0.811 | 0.917 | 0.917 | 0.828 | 0.833 | 0.917 | 0.917 |

Full table: `metrics/activity_holdout_metrics.csv`.

## 8. Synthetic-corruption robustness (change in recording-level balanced accuracy vs clean)

Controlled experiment with **synthetic** corruptions; it does not prove behaviour under real motion/EMG/ocular artefacts.

| noise_type | snr_db | E1 | E10 | E11 | E12B | E12T | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | FT-B-lin | FT-B-mlp | FT-B-vqc | FT-T-lin | FT-T-mlp | FT-T-vqc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_drift | +5.000 | -0.011 | -0.028 | -0.003 | +0.017 | -0.019 | +0.003 | +0.008 | -0.022 | -0.022 | -0.031 | -0.017 | -0.022 | -0.008 | -0.006 | +0.003 | -0.011 | -0.003 | -0.014 | -0.022 |
| baseline_drift | +10.000 | -0.006 | -0.008 | -0.019 | +0.011 | +0.006 | +0.011 | +0.008 | -0.014 | -0.019 | -0.011 | +0.000 | -0.019 | -0.008 | +0.006 | -0.003 | -0.003 | +0.011 | -0.003 | +0.003 |
| baseline_drift | +20.000 | +0.000 | +0.003 | +0.014 | +0.006 | +0.006 | -0.003 | +0.000 | -0.014 | -0.006 | -0.008 | +0.003 | -0.003 | +0.003 | +0.000 | +0.003 | +0.006 | +0.000 | +0.000 | -0.011 |
| emg_like | +5.000 | -0.200 | -0.206 | -0.186 | -0.206 | -0.239 | -0.172 | -0.194 | -0.247 | -0.239 | -0.225 | -0.197 | -0.242 | -0.239 | -0.206 | -0.200 | -0.231 | -0.233 | -0.244 | -0.219 |
| emg_like | +10.000 | -0.181 | -0.156 | -0.133 | -0.144 | -0.194 | -0.158 | -0.186 | -0.192 | -0.192 | -0.181 | -0.156 | -0.225 | -0.217 | -0.167 | -0.164 | -0.158 | -0.197 | -0.206 | -0.178 |
| emg_like | +20.000 | -0.014 | -0.017 | -0.014 | +0.008 | -0.050 | -0.006 | +0.000 | -0.047 | -0.031 | -0.025 | -0.025 | -0.014 | -0.011 | -0.006 | -0.000 | -0.025 | -0.061 | -0.061 | -0.047 |
| gaussian | +5.000 | -0.217 | -0.217 | -0.192 | -0.197 | -0.217 | -0.167 | -0.194 | -0.239 | -0.228 | -0.239 | -0.197 | -0.264 | -0.239 | -0.208 | -0.214 | -0.208 | -0.242 | -0.247 | -0.203 |
| gaussian | +10.000 | -0.156 | -0.164 | -0.175 | -0.158 | -0.189 | -0.103 | -0.128 | -0.178 | -0.186 | -0.164 | -0.150 | -0.231 | -0.219 | -0.169 | -0.164 | -0.164 | -0.189 | -0.186 | -0.161 |
| gaussian | +20.000 | -0.003 | -0.022 | -0.033 | -0.017 | -0.039 | -0.011 | -0.008 | -0.011 | -0.017 | -0.006 | +0.011 | -0.028 | -0.011 | +0.008 | +0.008 | -0.014 | -0.036 | -0.019 | -0.006 |
| ocular_like | +5.000 | -0.017 | -0.033 | -0.017 | +0.028 | -0.042 | -0.047 | +0.011 | -0.031 | -0.042 | -0.014 | -0.003 | -0.047 | -0.025 | +0.011 | -0.003 | +0.014 | -0.011 | -0.011 | -0.033 |
| ocular_like | +10.000 | +0.008 | +0.000 | -0.008 | -0.011 | -0.031 | +0.000 | +0.008 | -0.025 | -0.033 | -0.022 | -0.028 | -0.022 | -0.003 | +0.019 | -0.006 | +0.014 | +0.008 | +0.000 | -0.011 |
| ocular_like | +20.000 | +0.019 | -0.011 | -0.008 | +0.011 | -0.011 | +0.008 | -0.011 | +0.006 | -0.006 | -0.006 | +0.003 | -0.006 | -0.003 | +0.006 | +0.006 | -0.003 | +0.011 | +0.003 | +0.014 |


## 9. Training cost

| model | params | seconds | epochs |
|---|---|---|---|
| E1 | n/a | 1.6 | n/a |
| E10 | n/a | 0.1 | n/a |
| E11 | 31.0 | 14.5 | 48.8 |
| E12B | 31.0 | 10.1 | 39.6 |
| E12T | 31.0 | 13.2 | 52.4 |
| E2 | n/a | 1.1 | n/a |
| E3 | n/a | 7.6 | n/a |
| E4 | 7.0 | 0.2 | 17.1 |
| E5 | 49.0 | 0.3 | 25.7 |
| E6 | n/a | 0.1 | n/a |
| E7 | 31.0 | 15.4 | 52.9 |
| E8 | 7.0 | 0.2 | 19.8 |
| E9 | 49.0 | 0.2 | 20.8 |
| FT-B-lin | 14989.0 | 1.2 | 17.2 |
| FT-B-mlp | 15031.0 | 1.3 | 17.6 |
| FT-B-vqc | 15013.0 | 14.9 | 34.7 |
| FT-T-lin | 25741.0 | 2.0 | 17.3 |
| FT-T-mlp | 25783.0 | 2.4 | 21.7 |
| FT-T-vqc | 25765.0 | 15.7 | 31.3 |
| pretrain_bilstm | 14982.0 | 2.3 | 34.2 |
| pretrain_transformer | 25734.0 | 3.6 | 32.5 |


## 10. Interpretation (data-driven; see also results_interpretation.md)

- Highest pooled recording-level balanced accuracy among frozen/classical models: **E5 (T+MLP)** = 0.814 [0.745, 0.884]. Differences between nearby models are usually within the bootstrap CIs (n = 90 recordings), so this ranking is not a statistically established order.
- Transformer head, VQC (E7) minus E4 (T+Linear), recording-level balanced accuracy: -0.050 [-0.103, +0.002] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E5 (T+MLP), recording-level balanced accuracy: -0.053 [-0.095, -0.007] -> VQC lower and the CI excludes 0.
- Transformer head, VQC (E7) minus E6 (T+RBF-SVM), recording-level balanced accuracy: -0.036 [-0.085, +0.008] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E12T (T+VQC(noCNOT)), recording-level balanced accuracy: -0.006 [-0.045, +0.033] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E11 (B+VQC), recording-level balanced accuracy: +0.014 [-0.035, +0.062] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E8 (B+Linear), recording-level balanced accuracy: -0.064 [-0.117, -0.010] -> VQC lower and the CI excludes 0.
- Bi-LSTM head, VQC (E11) minus E9 (B+MLP), recording-level balanced accuracy: -0.044 [-0.091, +0.004] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E10 (B+RBF-SVM), recording-level balanced accuracy: -0.033 [-0.078, +0.015] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E12B (B+VQC(noCNOT)), recording-level balanced accuracy: -0.006 [-0.053, +0.034] -> no distinguishable difference (CI includes 0).
- Cost: VQC head trainable parameters = 31.0 vs MLP head = 49.0; mean head fitting time 15.4 s (VQC, classical simulation) vs 0.3 s (MLP). Simulation overhead is not evidence about quantum hardware.
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
