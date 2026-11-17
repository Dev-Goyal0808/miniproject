# Final experiment report

> Auto-generated from the numbers produced in this run. Nothing in this report is hard-coded or taken from the base paper. Profile: **enhanced**, seeds [0, 1, 2], 5 outer folds.

## 1. What was run

- Dataset: 90 recordings (60 healthy / 30 epilepsy), 360 windows of 5 s (non-overlapping).
- Evaluation unit: **recording** (mean of window probabilities, validation-selected threshold). Window-level metrics are secondary.
- Splits: grouped by recording (no participant IDs exist -> **no participant-independent claim**).
- Experiments: E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12T, E12B, FT-T-lin, FT-T-mlp, FT-T-vqc, FT-B-lin, FT-B-mlp, FT-B-vqc.

## 2. Primary results - recording level, frozen encoders and classical baselines

Pooled over all outer test folds, averaged over 3 seed(s); CI = 95% bootstrap over recordings. All models share identical folds, partitions and (for E4-E12) identical 6-D embeddings.

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.761 [0.684, 0.833] | 0.804 [0.733, 0.867] | 0.633 | 0.889 | 0.877 | 0.557 | 0.732 |
| E2 | GWST-450 + SVM | 0.764 [0.695, 0.835] | 0.822 [0.752, 0.881] | 0.589 | 0.939 | 0.890 | 0.584 | 0.713 |
| E3 | GWST-450 + MI selection + Random Forest | 0.717 [0.636, 0.793] | 0.759 [0.685, 0.826] | 0.589 | 0.844 | 0.848 | 0.450 | 0.703 |
| E4 | Transformer + 6-D embedding + linear | 0.814 [0.741, 0.881] | 0.833 [0.767, 0.893] | 0.756 | 0.872 | 0.900 | 0.628 | 0.756 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.814 [0.739, 0.882] | 0.837 [0.770, 0.900] | 0.744 | 0.883 | 0.902 | 0.633 | 0.758 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.781 [0.706, 0.854] | 0.819 [0.756, 0.881] | 0.667 | 0.894 | 0.897 | 0.582 | 0.756 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.786 [0.719, 0.856] | 0.811 [0.748, 0.874] | 0.711 | 0.861 | 0.892 | 0.578 | 0.741 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.794 [0.725, 0.866] | 0.811 [0.748, 0.874] | 0.744 | 0.844 | 0.902 | 0.581 | 0.753 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.775 [0.699, 0.847] | 0.796 [0.726, 0.859] | 0.711 | 0.839 | 0.903 | 0.546 | 0.758 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.783 [0.713, 0.852] | 0.804 [0.741, 0.863] | 0.722 | 0.844 | 0.891 | 0.573 | 0.731 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.756 [0.687, 0.824] | 0.759 [0.693, 0.826] | 0.744 | 0.767 | 0.884 | 0.495 | 0.730 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.811 [0.750, 0.875] | 0.826 [0.767, 0.882] | 0.767 | 0.856 | 0.894 | 0.615 | 0.755 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.769 [0.695, 0.844] | 0.789 [0.718, 0.852] | 0.711 | 0.828 | 0.900 | 0.532 | 0.756 |

Fold-wise mean ± sd (n = seeds x folds; NaN-aware):

| ID | Model | folds evaluated | Bal. acc. (mean ± sd over folds) | Accuracy (mean ± sd) | Macro-F1 | ROC-AUC (valid folds) | ROC-AUC n valid |
|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 15 | 0.761 ± 0.094 | 0.804 ± 0.081 | 0.762 | 0.891 | 15 |
| E2 | GWST-450 + SVM | 15 | 0.764 ± 0.103 | 0.822 ± 0.067 | 0.770 | 0.903 | 15 |
| E3 | GWST-450 + MI selection + Random Forest | 15 | 0.717 ± 0.087 | 0.759 ± 0.088 | 0.714 | 0.862 | 15 |
| E4 | Transformer + 6-D embedding + linear | 15 | 0.814 ± 0.098 | 0.833 ± 0.089 | 0.811 | 0.900 | 15 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 15 | 0.814 ± 0.096 | 0.837 ± 0.083 | 0.814 | 0.900 | 15 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 15 | 0.781 ± 0.091 | 0.819 ± 0.077 | 0.786 | 0.894 | 15 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 15 | 0.786 ± 0.079 | 0.811 ± 0.081 | 0.785 | 0.892 | 15 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 15 | 0.811 ± 0.089 | 0.826 ± 0.081 | 0.806 | 0.894 | 15 |
| E8 | Bi-LSTM + 6-D embedding + linear | 15 | 0.794 ± 0.111 | 0.811 ± 0.098 | 0.785 | 0.900 | 15 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 15 | 0.775 ± 0.102 | 0.796 ± 0.091 | 0.761 | 0.902 | 15 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 15 | 0.783 ± 0.097 | 0.804 ± 0.089 | 0.774 | 0.895 | 15 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 15 | 0.756 ± 0.112 | 0.759 ± 0.102 | 0.736 | 0.891 | 15 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 15 | 0.769 ± 0.108 | 0.789 ± 0.103 | 0.756 | 0.895 | 15 |

## 3. End-to-end fine-tuned models (separate comparison - not comparable 1:1 with Section 2)

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| FT-T-lin | [fine-tuned] Transformer + linear | 0.808 [0.735, 0.879] | 0.837 [0.770, 0.900] | 0.722 | 0.894 | 0.903 | 0.628 | 0.756 |
| FT-T-mlp | [fine-tuned] Transformer + MLP | 0.817 [0.749, 0.883] | 0.844 [0.781, 0.904] | 0.733 | 0.900 | 0.895 | 0.645 | 0.761 |
| FT-T-vqc | [fine-tuned] Transformer + VQC | 0.797 [0.721, 0.876] | 0.830 [0.759, 0.893] | 0.700 | 0.894 | 0.903 | 0.612 | 0.747 |
| FT-B-lin | [fine-tuned] Bi-LSTM + linear | 0.781 [0.703, 0.861] | 0.800 [0.730, 0.874] | 0.722 | 0.839 | 0.897 | 0.557 | 0.742 |
| FT-B-mlp | [fine-tuned] Bi-LSTM + MLP | 0.792 [0.719, 0.866] | 0.796 [0.726, 0.863] | 0.778 | 0.806 | 0.898 | 0.564 | 0.756 |
| FT-B-vqc | [fine-tuned] Bi-LSTM + VQC | 0.781 [0.707, 0.852] | 0.796 [0.722, 0.859] | 0.733 | 0.828 | 0.898 | 0.555 | 0.746 |


## 4. Primary results restricted to activities present in both classes

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.763 [0.682, 0.836] | 0.792 [0.714, 0.861] | 0.633 | 0.894 | 0.879 | 0.566 | 0.733 |
| E2 | GWST-450 + SVM | 0.759 [0.686, 0.833] | 0.797 [0.719, 0.870] | 0.589 | 0.929 | 0.876 | 0.566 | 0.703 |
| E3 | GWST-450 + MI selection + Random Forest | 0.713 [0.620, 0.791] | 0.740 [0.654, 0.814] | 0.589 | 0.837 | 0.843 | 0.445 | 0.701 |
| E4 | Transformer + 6-D embedding + linear | 0.800 [0.722, 0.871] | 0.810 [0.736, 0.875] | 0.756 | 0.844 | 0.882 | 0.601 | 0.742 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.801 [0.721, 0.871] | 0.814 [0.736, 0.879] | 0.744 | 0.858 | 0.882 | 0.608 | 0.743 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.766 [0.683, 0.841] | 0.788 [0.714, 0.861] | 0.667 | 0.865 | 0.875 | 0.547 | 0.738 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.774 [0.696, 0.845] | 0.788 [0.710, 0.857] | 0.711 | 0.837 | 0.872 | 0.555 | 0.722 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.776 [0.696, 0.849] | 0.784 [0.706, 0.853] | 0.744 | 0.809 | 0.881 | 0.549 | 0.732 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.760 [0.680, 0.835] | 0.771 [0.693, 0.840] | 0.711 | 0.809 | 0.882 | 0.519 | 0.737 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.765 [0.688, 0.837] | 0.775 [0.701, 0.840] | 0.722 | 0.809 | 0.867 | 0.540 | 0.713 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.730 [0.654, 0.802] | 0.727 [0.649, 0.801] | 0.744 | 0.716 | 0.861 | 0.457 | 0.710 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.802 [0.729, 0.867] | 0.810 [0.736, 0.874] | 0.767 | 0.837 | 0.874 | 0.603 | 0.742 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.753 [0.673, 0.829] | 0.762 [0.684, 0.840] | 0.711 | 0.794 | 0.879 | 0.503 | 0.737 |


## 5. Matched classical-vs-quantum comparison (same embeddings)

Difference = model_a - model_b in recording-level metric; CI from paired bootstrap over recordings; McNemar exact p per seed (uncorrected, exploratory).

| model_a | model_b | mean_difference_a_minus_b | ci_low | ci_high | ci_excludes_zero | mcnemar_a_only_correct | mcnemar_b_only_correct | mcnemar_exact_p_per_seed |
|---|---|---|---|---|---|---|---|---|
| E7 | E4 | -0.028 | -0.070 | 0.022 | False | 10.000 | 16.000 | 0.375;1.000;0.727 |
| E7 | E5 | -0.028 | -0.068 | 0.018 | False | 8.000 | 15.000 | 0.625;1.000;0.289 |
| E7 | E6 | 0.006 | -0.026 | 0.041 | False | 8.000 | 10.000 | 0.625;1.000;1.000 |
| E7 | E12T | -0.025 | -0.062 | 0.011 | False | 11.000 | 15.000 | 1.000;1.000;0.754 |
| E11 | E8 | -0.039 | -0.086 | 0.006 | False | 9.000 | 23.000 | 0.289;0.302;0.180 |
| E11 | E9 | -0.019 | -0.067 | 0.029 | False | 14.000 | 24.000 | 0.388;1.000;0.070 |
| E11 | E10 | -0.028 | -0.072 | 0.017 | False | 13.000 | 25.000 | 0.180;1.000;0.267 |
| E11 | E12B | -0.014 | -0.063 | 0.041 | False | 15.000 | 23.000 | 0.549;1.000;0.109 |
| E4 | E8 | 0.019 | -0.035 | 0.073 | False | 23.000 | 17.000 | 0.146;1.000;1.000 |
| E5 | E9 | 0.039 | -0.021 | 0.099 | False | 28.000 | 17.000 | 0.227;0.503;0.791 |
| E6 | E10 | -0.003 | -0.053 | 0.051 | False | 24.000 | 20.000 | 0.508;1.000;1.000 |
| E7 | E11 | 0.031 | -0.033 | 0.096 | False | 37.000 | 23.000 | 0.143;0.678;0.503 |
| E1 | E2 | -0.003 | -0.067 | 0.064 | False | 22.000 | 27.000 | 0.791;1.000;0.057 |
| E1 | E3 | 0.044 | 0.002 | 0.094 | True | 18.000 | 6.000 | 0.039;0.727;0.453 |
| FT-T-vqc | FT-T-lin | -0.011 | -0.059 | 0.031 | False | 11.000 | 13.000 | 0.375;0.344;0.508 |
| FT-T-vqc | FT-T-mlp | -0.019 | -0.069 | 0.021 | False | 11.000 | 15.000 | 0.375;0.549;0.344 |
| FT-B-vqc | FT-B-lin | 0.000 | -0.046 | 0.046 | False | 15.000 | 16.000 | 1.000;0.774;1.000 |
| FT-B-vqc | FT-B-mlp | -0.011 | -0.052 | 0.031 | False | 12.000 | 12.000 | 1.000;1.000;1.000 |


## 6. Activity-wise and activity-group results (recording-level accuracy; pooled outer-CV test predictions)

Per-activity sample sizes are tiny (2-10 recordings per class); treat as descriptive. Healthy-only activities can only yield accuracy = specificity.

| unit | E1 | E11 | E2 | E5 | E7 | E9 |
|---|---|---|---|---|---|---|
| cooking | 0.556 | 1.000 | 0.889 | 0.889 | 0.889 | 1.000 |
| desk work | 0.867 | 0.700 | 0.767 | 0.800 | 0.800 | 0.767 |
| idle sitting | 0.714 | 0.619 | 0.762 | 0.762 | 0.762 | 0.571 |
| intense_ambulatory | 0.745 | 0.804 | 0.824 | 0.784 | 0.706 | 0.824 |
| jogging | 0.778 | 0.852 | 0.963 | 0.889 | 0.815 | 0.889 |
| jumping | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| laying | 0.333 | 0.533 | 0.400 | 0.600 | 0.400 | 0.400 |
| light_ambulatory | 0.893 | 0.810 | 0.881 | 0.905 | 0.917 | 0.869 |
| running | 0.708 | 0.750 | 0.667 | 0.667 | 0.583 | 0.750 |
| sitting | 0.800 | 0.567 | 0.767 | 0.767 | 0.767 | 0.733 |
| stairs | 0.889 | 0.694 | 0.833 | 0.806 | 0.833 | 0.806 |
| standing | 0.833 | 0.667 | 1.000 | 1.000 | 0.833 | 0.667 |
| stationary | 0.729 | 0.615 | 0.708 | 0.750 | 0.719 | 0.656 |
| walking | 0.896 | 0.896 | 0.917 | 0.979 | 0.979 | 0.917 |
| watching tv | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |


## 7. Leave-one-activity-out (recording-level balanced accuracy)

Train on the other eligible activities, test on the held-out activity (complete recordings; validation partition drawn from training activities only).

| heldout | E1 | E10 | E11 | E12B | E12T | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| desk work | 0.659 | 0.706 | 0.563 | 0.786 | 0.730 | 0.476 | 0.627 | 0.706 | 0.706 | 0.675 | 0.675 | 0.762 | 0.762 |
| idle sitting | 0.722 | 0.431 | 0.431 | 0.500 | 0.722 | 0.556 | 0.542 | 0.722 | 0.667 | 0.542 | 0.667 | 0.431 | 0.431 |
| jogging | 0.444 | 0.778 | 0.833 | 0.806 | 0.778 | 0.556 | 0.444 | 0.778 | 0.806 | 0.750 | 0.750 | 0.806 | 0.833 |
| laying | 0.250 | 0.222 | 0.333 | 0.333 | 0.500 | 0.389 | 0.250 | 0.500 | 0.500 | 0.500 | 0.500 | 0.417 | 0.333 |
| running | 0.444 | 0.567 | 0.678 | 0.567 | 0.456 | 0.589 | 0.511 | 0.456 | 0.456 | 0.456 | 0.456 | 0.567 | 0.567 |
| sitting | 0.611 | 0.460 | 0.516 | 0.579 | 0.310 | 0.492 | 0.579 | 0.381 | 0.421 | 0.365 | 0.389 | 0.492 | 0.516 |
| stairs | 0.611 | 0.806 | 0.806 | 0.722 | 0.667 | 0.806 | 0.611 | 0.694 | 0.667 | 0.722 | 0.722 | 0.806 | 0.806 |
| walking | 0.678 | 0.783 | 0.750 | 0.789 | 0.839 | 0.917 | 0.733 | 0.928 | 0.900 | 0.828 | 0.900 | 0.889 | 0.889 |

Full table: `metrics/activity_holdout_metrics.csv`.

## 8. Synthetic-corruption robustness (change in recording-level balanced accuracy vs clean)

Controlled experiment with **synthetic** corruptions; it does not prove behaviour under real motion/EMG/ocular artefacts.

| noise_type | snr_db | E1 | E10 | E11 | E12B | E12T | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | FT-B-lin | FT-B-mlp | FT-B-vqc | FT-T-lin | FT-T-mlp | FT-T-vqc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_drift | +5.000 | -0.006 | +0.000 | -0.003 | +0.011 | -0.011 | -0.011 | +0.008 | -0.017 | -0.008 | -0.011 | -0.014 | +0.003 | +0.011 | -0.014 | +0.000 | -0.003 | -0.025 | -0.011 | -0.022 |
| baseline_drift | +10.000 | -0.006 | +0.000 | +0.006 | +0.025 | -0.011 | +0.006 | +0.006 | -0.011 | -0.006 | -0.006 | -0.003 | +0.011 | +0.019 | +0.011 | +0.019 | -0.003 | -0.003 | -0.003 | +0.000 |
| baseline_drift | +20.000 | +0.003 | -0.008 | -0.003 | +0.000 | -0.008 | -0.003 | +0.000 | +0.000 | -0.006 | +0.000 | +0.008 | +0.003 | +0.003 | +0.003 | +0.003 | +0.000 | -0.006 | -0.008 | -0.006 |
| emg_like | +5.000 | -0.228 | -0.231 | -0.192 | -0.211 | -0.253 | -0.183 | -0.206 | -0.253 | -0.253 | -0.219 | -0.219 | -0.228 | -0.206 | -0.225 | -0.236 | -0.225 | -0.261 | -0.264 | -0.233 |
| emg_like | +10.000 | -0.194 | -0.169 | -0.147 | -0.172 | -0.206 | -0.161 | -0.156 | -0.225 | -0.222 | -0.172 | -0.147 | -0.192 | -0.183 | -0.172 | -0.178 | -0.189 | -0.214 | -0.203 | -0.208 |
| emg_like | +20.000 | -0.017 | -0.019 | +0.003 | -0.008 | -0.047 | -0.017 | +0.008 | -0.028 | -0.033 | -0.022 | -0.039 | +0.003 | -0.003 | -0.014 | +0.006 | -0.025 | -0.025 | -0.031 | -0.008 |
| gaussian | +5.000 | -0.222 | -0.231 | -0.208 | -0.208 | -0.233 | -0.206 | -0.208 | -0.242 | -0.236 | -0.189 | -0.228 | -0.211 | -0.219 | -0.200 | -0.236 | -0.231 | -0.242 | -0.258 | -0.242 |
| gaussian | +10.000 | -0.175 | -0.169 | -0.164 | -0.133 | -0.172 | -0.122 | -0.133 | -0.192 | -0.189 | -0.172 | -0.161 | -0.172 | -0.164 | -0.158 | -0.150 | -0.186 | -0.183 | -0.194 | -0.183 |
| gaussian | +20.000 | -0.003 | -0.017 | +0.006 | +0.000 | -0.028 | -0.003 | +0.011 | -0.031 | -0.022 | -0.017 | -0.022 | +0.006 | +0.003 | -0.008 | -0.003 | -0.017 | -0.006 | -0.025 | -0.003 |
| ocular_like | +5.000 | -0.025 | -0.019 | +0.028 | +0.008 | +0.014 | -0.056 | +0.006 | -0.019 | -0.025 | -0.019 | -0.008 | -0.003 | +0.008 | -0.003 | +0.003 | -0.003 | -0.031 | -0.025 | -0.008 |
| ocular_like | +10.000 | -0.003 | -0.028 | +0.025 | -0.006 | +0.003 | -0.006 | +0.006 | -0.008 | -0.019 | +0.006 | +0.017 | +0.008 | +0.008 | +0.014 | +0.003 | -0.008 | +0.006 | -0.028 | -0.008 |
| ocular_like | +20.000 | -0.014 | +0.008 | +0.006 | +0.000 | -0.006 | +0.008 | +0.003 | +0.000 | +0.003 | +0.003 | -0.006 | +0.000 | +0.003 | -0.003 | +0.003 | -0.003 | +0.006 | -0.003 | +0.000 |


## 9. Training cost

| model | params | seconds | epochs |
|---|---|---|---|
| E1 | n/a | 15.2 | n/a |
| E10 | n/a | 0.1 | n/a |
| E11 | 55.0 | 18.9 | 56.5 |
| E12B | 55.0 | 13.2 | 46.3 |
| E12T | 55.0 | 11.6 | 38.8 |
| E2 | n/a | 0.9 | n/a |
| E3 | n/a | 79.5 | n/a |
| E4 | 7.0 | 0.3 | 39.4 |
| E5 | 49.0 | 0.4 | 41.2 |
| E6 | n/a | 0.1 | n/a |
| E7 | 55.0 | 19.9 | 57.4 |
| E8 | 7.0 | 0.3 | 43.6 |
| E9 | 49.0 | 0.4 | 39.8 |
| FT-B-lin | 14989.0 | 2.4 | 34.9 |
| FT-B-mlp | 15031.0 | 1.9 | 27.3 |
| FT-B-vqc | 15037.0 | 26.7 | 54.9 |
| FT-T-lin | 25741.0 | 3.2 | 32.1 |
| FT-T-mlp | 25783.0 | 3.0 | 29.5 |
| FT-T-vqc | 25789.0 | 22.4 | 38.9 |
| pretrain_bilstm | 14982.0 | 4.3 | 66.3 |
| pretrain_transformer | 25734.0 | 6.2 | 60.4 |


## 10. Interpretation (data-driven; see also results_interpretation.md)

- Highest pooled recording-level balanced accuracy among frozen/classical models: **E5 (T+MLP)** = 0.814 [0.739, 0.882]. Differences between nearby models are usually within the bootstrap CIs (n = 90 recordings), so this ranking is not a statistically established order.
- Transformer head, VQC (E7) minus E4 (T+Linear), recording-level balanced accuracy: -0.028 [-0.070, +0.022] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E5 (T+MLP), recording-level balanced accuracy: -0.028 [-0.068, +0.018] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E6 (T+RBF-SVM), recording-level balanced accuracy: +0.006 [-0.026, +0.041] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E12T (T+VQC(noCNOT)), recording-level balanced accuracy: -0.025 [-0.062, +0.011] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E11 (B+VQC), recording-level balanced accuracy: +0.031 [-0.033, +0.096] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E8 (B+Linear), recording-level balanced accuracy: -0.039 [-0.086, +0.006] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E9 (B+MLP), recording-level balanced accuracy: -0.019 [-0.067, +0.029] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E10 (B+RBF-SVM), recording-level balanced accuracy: -0.028 [-0.072, +0.017] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E12B (B+VQC(noCNOT)), recording-level balanced accuracy: -0.014 [-0.063, +0.041] -> no distinguishable difference (CI includes 0).
- Cost: VQC head trainable parameters = 55.0 vs MLP head = 49.0; mean head fitting time 19.9 s (VQC, classical simulation) vs 0.4 s (MLP). Simulation overhead is not evidence about quantum hardware.
- The 6-D embedding for the frozen comparison was pre-trained with a mlp head; heads of that type may be favoured.
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
