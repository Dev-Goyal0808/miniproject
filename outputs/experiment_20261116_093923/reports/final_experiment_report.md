# Final experiment report

> Auto-generated from the numbers produced in this run. Nothing in this report is hard-coded or taken from the base paper. Profile: **smoke**, seeds [0], 5 outer folds (restricted to 2).

## 1. What was run

- Dataset: 90 recordings (60 healthy / 30 epilepsy), 360 windows of 5 s (non-overlapping).
- Evaluation unit: **recording** (mean of window probabilities, validation-selected threshold). Window-level metrics are secondary.
- Splits: grouped by recording (no participant IDs exist -> **no participant-independent claim**).
- Experiments: E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12T, E12B, FT-T-lin, FT-T-mlp, FT-T-vqc, FT-B-lin, FT-B-mlp, FT-B-vqc.

## 2. Primary results - recording level, frozen encoders and classical baselines

Pooled over all outer test folds, averaged over 1 seed(s); CI = 95% bootstrap over recordings. All models share identical folds, partitions and (for E4-E12) identical 6-D embeddings.

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.812 [0.630, 0.948] | 0.833 [0.667, 0.944] | 0.750 | 0.875 | 0.889 | 0.625 | 0.760 |
| E2 | GWST-450 + SVM | 0.896 [0.785, 0.992] | 0.917 [0.833, 0.987] | 0.833 | 0.958 | 0.986 | 0.810 | 0.781 |
| E3 | GWST-450 + MI selection + Random Forest | 0.688 [0.484, 0.863] | 0.694 [0.541, 0.862] | 0.667 | 0.708 | 0.802 | 0.359 | 0.677 |
| E4 | Transformer + 6-D embedding + linear | 0.792 [0.652, 0.934] | 0.778 [0.652, 0.917] | 0.833 | 0.750 | 0.882 | 0.553 | 0.766 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.771 [0.639, 0.919] | 0.750 [0.639, 0.889] | 0.833 | 0.708 | 0.878 | 0.511 | 0.776 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.854 [0.735, 0.981] | 0.861 [0.778, 0.972] | 0.833 | 0.875 | 0.920 | 0.695 | 0.786 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.729 [0.617, 0.852] | 0.667 [0.500, 0.806] | 0.917 | 0.542 | 0.785 | 0.443 | 0.682 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.875 [0.766, 1.000] | 0.889 [0.806, 1.000] | 0.833 | 0.917 | 0.920 | 0.750 | 0.802 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.875 [0.766, 1.000] | 0.889 [0.806, 1.000] | 0.833 | 0.917 | 0.899 | 0.750 | 0.792 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.833 [0.734, 0.983] | 0.861 [0.750, 0.972] | 0.750 | 0.917 | 0.910 | 0.682 | 0.818 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.729 [0.557, 0.883] | 0.750 [0.597, 0.903] | 0.667 | 0.792 | 0.816 | 0.450 | 0.599 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.771 [0.646, 0.941] | 0.806 [0.694, 0.944] | 0.667 | 0.875 | 0.858 | 0.554 | 0.776 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.771 [0.656, 0.947] | 0.778 [0.667, 0.917] | 0.750 | 0.792 | 0.882 | 0.524 | 0.802 |

Fold-wise mean ± sd (n = seeds x folds; NaN-aware):

| ID | Model | folds evaluated | Bal. acc. (mean ± sd over folds) | Accuracy (mean ± sd) | Macro-F1 | ROC-AUC (valid folds) | ROC-AUC n valid |
|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 2 | 0.812 ± 0.029 | 0.833 ± 0.079 | 0.814 | 0.889 | 2 |
| E2 | GWST-450 + SVM | 2 | 0.896 ± 0.147 | 0.917 ± 0.118 | 0.902 | 0.972 | 2 |
| E3 | GWST-450 + MI selection + Random Forest | 2 | 0.688 ± 0.029 | 0.694 ± 0.039 | 0.674 | 0.816 | 2 |
| E4 | Transformer + 6-D embedding + linear | 2 | 0.792 ± 0.059 | 0.778 ± 0.079 | 0.767 | 0.882 | 2 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 2 | 0.771 ± 0.088 | 0.750 ± 0.118 | 0.741 | 0.889 | 2 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 2 | 0.854 ± 0.029 | 0.861 ± 0.039 | 0.847 | 0.924 | 2 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 2 | 0.729 ± 0.029 | 0.667 ± 0.079 | 0.662 | 0.771 | 2 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 2 | 0.771 ± 0.029 | 0.806 ± 0.039 | 0.772 | 0.882 | 2 |
| E8 | Bi-LSTM + 6-D embedding + linear | 2 | 0.875 ± 0.000 | 0.889 ± 0.000 | 0.875 | 0.924 | 2 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 2 | 0.875 ± 0.000 | 0.889 ± 0.000 | 0.875 | 0.903 | 2 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 2 | 0.833 ± 0.059 | 0.861 ± 0.039 | 0.839 | 0.917 | 2 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 2 | 0.729 ± 0.088 | 0.750 ± 0.118 | 0.726 | 0.812 | 2 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 2 | 0.771 ± 0.029 | 0.778 ± 0.079 | 0.759 | 0.882 | 2 |

## 3. End-to-end fine-tuned models (separate comparison - not comparable 1:1 with Section 2)

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| FT-T-lin | [fine-tuned] Transformer + linear | 0.833 [0.716, 0.959] | 0.833 [0.750, 0.944] | 0.833 | 0.833 | 0.892 | 0.645 | 0.807 |
| FT-T-mlp | [fine-tuned] Transformer + MLP | 0.833 [0.716, 0.959] | 0.833 [0.750, 0.944] | 0.833 | 0.833 | 0.885 | 0.645 | 0.812 |
| FT-T-vqc | [fine-tuned] Transformer + VQC | 0.812 [0.701, 0.946] | 0.806 [0.708, 0.917] | 0.833 | 0.792 | 0.896 | 0.598 | 0.750 |
| FT-B-lin | [fine-tuned] Bi-LSTM + linear | 0.854 [0.735, 0.981] | 0.861 [0.778, 0.972] | 0.833 | 0.875 | 0.924 | 0.695 | 0.818 |
| FT-B-mlp | [fine-tuned] Bi-LSTM + MLP | 0.875 [0.766, 1.000] | 0.889 [0.806, 1.000] | 0.833 | 0.917 | 0.906 | 0.750 | 0.823 |
| FT-B-vqc | [fine-tuned] Bi-LSTM + VQC | 0.771 [0.639, 0.900] | 0.833 [0.708, 0.959] | 0.583 | 0.958 | 0.865 | 0.614 | 0.719 |


## 4. Primary results restricted to activities present in both classes

| ID | Model | Bal. acc. [95% CI] | Accuracy [95% CI] | Sensitivity | Specificity | ROC-AUC | MCC | Window bal. acc. |
|---|---|---|---|---|---|---|---|---|
| E1 | GWST-450 + Random Forest | 0.819 [0.682, 0.958] | 0.833 [0.700, 0.967] | 0.750 | 0.889 | 0.889 | 0.649 | 0.764 |
| E2 | GWST-450 + SVM | 0.917 [0.802, 1.000] | 0.933 [0.849, 1.000] | 0.833 | 1.000 | 0.991 | 0.866 | 0.771 |
| E3 | GWST-450 + MI selection + Random Forest | 0.722 [0.572, 0.888] | 0.733 [0.600, 0.884] | 0.667 | 0.778 | 0.819 | 0.444 | 0.705 |
| E4 | Transformer + 6-D embedding + linear | 0.833 [0.665, 0.974] | 0.833 [0.682, 0.967] | 0.833 | 0.833 | 0.907 | 0.659 | 0.788 |
| E5 | Transformer + 6-D embedding + MLP(6-6-1) | 0.806 [0.662, 0.955] | 0.800 [0.667, 0.933] | 0.833 | 0.778 | 0.898 | 0.600 | 0.795 |
| E6 | Transformer + 6-D embedding + RBF-SVM | 0.833 [0.665, 0.974] | 0.833 [0.682, 0.967] | 0.833 | 0.833 | 0.912 | 0.659 | 0.774 |
| E7 | Transformer + 6-D embedding + 6-qubit VQC | 0.708 [0.561, 0.849] | 0.667 [0.500, 0.833] | 0.917 | 0.500 | 0.782 | 0.433 | 0.660 |
| E8 | Bi-LSTM + 6-D embedding + linear | 0.861 [0.721, 0.978] | 0.867 [0.749, 0.967] | 0.833 | 0.889 | 0.903 | 0.722 | 0.792 |
| E9 | Bi-LSTM + 6-D embedding + MLP(6-6-1) | 0.861 [0.721, 0.978] | 0.867 [0.749, 0.967] | 0.833 | 0.889 | 0.884 | 0.722 | 0.778 |
| E10 | Bi-LSTM + 6-D embedding + RBF-SVM | 0.819 [0.625, 0.975] | 0.833 [0.667, 0.967] | 0.750 | 0.889 | 0.898 | 0.649 | 0.806 |
| E11 | Bi-LSTM + 6-D embedding + 6-qubit VQC | 0.722 [0.559, 0.902] | 0.733 [0.600, 0.900] | 0.667 | 0.778 | 0.801 | 0.444 | 0.590 |
| E12T | Transformer + 6-D embedding + VQC without CNOT | 0.778 [0.557, 0.929] | 0.800 [0.600, 0.933] | 0.667 | 0.889 | 0.880 | 0.577 | 0.788 |
| E12B | Bi-LSTM + 6-D embedding + VQC without CNOT | 0.736 [0.559, 0.915] | 0.733 [0.583, 0.900] | 0.750 | 0.722 | 0.852 | 0.464 | 0.788 |


## 5. Matched classical-vs-quantum comparison (same embeddings)

Difference = model_a - model_b in recording-level metric; CI from paired bootstrap over recordings; McNemar exact p per seed (uncorrected, exploratory).

| model_a | model_b | mean_difference_a_minus_b | ci_low | ci_high | ci_excludes_zero | mcnemar_a_only_correct | mcnemar_b_only_correct | mcnemar_exact_p_per_seed |
|---|---|---|---|---|---|---|---|---|
| E7 | E4 | -0.063 | -0.201 | 0.038 | False | 2.000 | 6.000 | 0.289 |
| E7 | E5 | -0.042 | -0.187 | 0.058 | False | 3.000 | 6.000 | 0.508 |
| E7 | E6 | -0.125 | -0.271 | -0.019 | True | 1.000 | 8.000 | 0.039 |
| E7 | E12T | -0.042 | -0.231 | 0.101 | False | 4.000 | 9.000 | 0.267 |
| E11 | E8 | -0.146 | -0.350 | 0.000 | False | 2.000 | 7.000 | 0.180 |
| E11 | E9 | -0.146 | -0.350 | 0.000 | False | 2.000 | 7.000 | 0.180 |
| E11 | E10 | -0.104 | -0.343 | 0.079 | False | 3.000 | 7.000 | 0.344 |
| E11 | E12B | -0.042 | -0.277 | 0.155 | False | 4.000 | 5.000 | 1.000 |
| E4 | E8 | -0.083 | -0.174 | -0.020 | True | 0.000 | 4.000 | 0.125 |
| E5 | E9 | -0.104 | -0.191 | -0.041 | True | 0.000 | 5.000 | 0.062 |
| E6 | E10 | 0.021 | -0.038 | 0.114 | False | 1.000 | 1.000 | 1.000 |
| E7 | E11 | 0.000 | -0.217 | 0.242 | False | 6.000 | 9.000 | 0.607 |
| E1 | E2 | -0.083 | -0.240 | 0.066 | False | 2.000 | 5.000 | 0.453 |
| E1 | E3 | 0.125 | 0.019 | 0.250 | True | 6.000 | 1.000 | 0.125 |
| FT-T-vqc | FT-T-lin | -0.021 | -0.077 | 0.045 | False | 1.000 | 2.000 | 1.000 |
| FT-T-vqc | FT-T-mlp | -0.021 | -0.077 | 0.045 | False | 1.000 | 2.000 | 1.000 |
| FT-B-vqc | FT-B-lin | -0.083 | -0.200 | 0.018 | False | 2.000 | 3.000 | 1.000 |
| FT-B-vqc | FT-B-mlp | -0.104 | -0.220 | 0.000 | False | 1.000 | 3.000 | 0.625 |


## 6. Activity-wise and activity-group results (recording-level accuracy; pooled outer-CV test predictions)

Per-activity sample sizes are tiny (2-10 recordings per class); treat as descriptive. Healthy-only activities can only yield accuracy = specificity.

| unit | E1 | E11 | E2 | E5 | E7 | E9 |
|---|---|---|---|---|---|---|
| cooking | 1.000 | 1.000 | 0.500 | 0.000 | 0.500 | 1.000 |
| desk work | 0.750 | 0.250 | 1.000 | 0.500 | 0.750 | 0.750 |
| idle sitting | 0.750 | 1.000 | 1.000 | 0.750 | 0.250 | 0.750 |
| intense_ambulatory | 0.833 | 0.500 | 0.833 | 0.833 | 0.500 | 0.833 |
| jogging | 0.750 | 0.500 | 0.750 | 0.750 | 0.750 | 0.750 |
| jumping | 0.500 | 1.000 | 1.000 | 0.500 | 0.500 | 1.000 |
| laying | 0.000 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 |
| light_ambulatory | 1.000 | 0.917 | 1.000 | 0.917 | 0.833 | 1.000 |
| running | 1.000 | 0.500 | 1.000 | 1.000 | 0.000 | 1.000 |
| sitting | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| stairs | 1.000 | 0.833 | 1.000 | 0.833 | 0.833 | 1.000 |
| standing | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| stationary | 0.667 | 0.667 | 0.917 | 0.667 | 0.583 | 0.750 |
| walking | 1.000 | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 |


## 7. Leave-one-activity-out (recording-level balanced accuracy)

Train on the other eligible activities, test on the held-out activity (complete recordings; validation partition drawn from training activities only).

| heldout | E1 | E4 | E7 | E8 |
|---|---|---|---|---|
| desk work | 0.786 | 0.643 | 0.500 | 0.524 |
| idle sitting | 0.500 | 0.500 | 0.500 | 0.500 |

Full table: `metrics/activity_holdout_metrics.csv`.

## 8. Synthetic-corruption robustness (change in recording-level balanced accuracy vs clean)

Controlled experiment with **synthetic** corruptions; it does not prove behaviour under real motion/EMG/ocular artefacts.

| noise_type | snr_db | E1 | E10 | E11 | E12B | E12T | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 | FT-B-lin | FT-B-mlp | FT-B-vqc | FT-T-lin | FT-T-mlp | FT-T-vqc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| emg_like | +10.000 | -0.167 | -0.167 | -0.042 | -0.167 | -0.208 | -0.229 | -0.042 | -0.271 | -0.250 | -0.292 | -0.104 | -0.292 | -0.312 | -0.271 | -0.312 | -0.083 | -0.333 | -0.333 | -0.208 |
| gaussian | +10.000 | -0.125 | -0.208 | -0.104 | -0.167 | -0.167 | -0.208 | -0.104 | -0.250 | -0.250 | -0.229 | -0.125 | -0.250 | -0.250 | -0.229 | -0.292 | -0.042 | -0.312 | -0.312 | -0.229 |


## 9. Training cost

| model | params | seconds | epochs |
|---|---|---|---|
| E1 | n/a | 0.0 | n/a |
| E10 | n/a | 0.0 | n/a |
| E11 | 31.0 | 0.8 | 3.0 |
| E12B | 31.0 | 0.7 | 3.0 |
| E12T | 31.0 | 0.7 | 3.0 |
| E2 | n/a | 0.0 | n/a |
| E3 | n/a | 0.5 | n/a |
| E4 | 7.0 | 0.0 | 3.0 |
| E5 | 49.0 | 0.0 | 3.0 |
| E6 | n/a | 0.0 | n/a |
| E7 | 31.0 | 0.8 | 3.0 |
| E8 | 7.0 | 0.0 | 3.0 |
| E9 | 49.0 | 0.0 | 3.0 |
| FT-B-lin | 14989.0 | 0.1 | 2.0 |
| FT-B-mlp | 15031.0 | 0.2 | 2.0 |
| FT-B-vqc | 15013.0 | 0.7 | 2.0 |
| FT-T-lin | 25741.0 | 0.2 | 2.0 |
| FT-T-mlp | 25783.0 | 0.3 | 2.0 |
| FT-T-vqc | 25765.0 | 0.8 | 2.0 |
| pretrain_bilstm | 14982.0 | 0.2 | 3.0 |
| pretrain_transformer | 25734.0 | 1.2 | 3.0 |


## 10. Interpretation (data-driven; see also results_interpretation.md)

- Highest pooled recording-level balanced accuracy among frozen/classical models: **E2 (SVM-450)** = 0.896 [0.785, 0.992]. Differences between nearby models are usually within the bootstrap CIs (n = 36 recordings), so this ranking is not a statistically established order.
- Transformer head, VQC (E7) minus E4 (T+Linear), recording-level balanced accuracy: -0.063 [-0.201, +0.038] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E5 (T+MLP), recording-level balanced accuracy: -0.042 [-0.187, +0.058] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E6 (T+RBF-SVM), recording-level balanced accuracy: -0.125 [-0.271, -0.019] -> VQC lower and the CI excludes 0.
- Transformer head, VQC (E7) minus E12T (T+VQC(noCNOT)), recording-level balanced accuracy: -0.042 [-0.231, +0.101] -> no distinguishable difference (CI includes 0).
- Transformer head, VQC (E7) minus E11 (B+VQC), recording-level balanced accuracy: +0.000 [-0.217, +0.242] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E8 (B+Linear), recording-level balanced accuracy: -0.146 [-0.350, +0.000] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E9 (B+MLP), recording-level balanced accuracy: -0.146 [-0.350, +0.000] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E10 (B+RBF-SVM), recording-level balanced accuracy: -0.104 [-0.343, +0.079] -> no distinguishable difference (CI includes 0).
- Bi-LSTM head, VQC (E11) minus E12B (B+VQC(noCNOT)), recording-level balanced accuracy: -0.042 [-0.277, +0.155] -> no distinguishable difference (CI includes 0).
- Cost: VQC head trainable parameters = 31.0 vs MLP head = 49.0; mean head fitting time 0.8 s (VQC, classical simulation) vs 0.0 s (MLP). Simulation overhead is not evidence about quantum hardware.
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
