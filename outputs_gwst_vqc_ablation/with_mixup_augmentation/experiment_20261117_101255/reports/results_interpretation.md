# Results interpretation

Automatically derived, intentionally conservative statements (profile `quick`).

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
- Cost: VQC head trainable parameters = 31.0 vs MLP head = 49.0; mean head fitting time 11.1 s (VQC, classical simulation) vs 0.1 s (MLP). Simulation overhead is not evidence about quantum hardware.
- The 6-D embedding for the frozen comparison was pre-trained with a linear head; heads of that type may be favoured.
- **Quantum-advantage statement:** this study simulates a 6-qubit circuit on a classical machine and compares it with matched classical heads on one small dataset. No paired comparison shows the VQC to be better than a matched classical head with a CI excluding 0. In no case is quantum advantage or supremacy claimed.

## Reading guide

- Prefer recording-level metrics; window-level numbers are correlated within recordings.
- Compare VQC only with heads on the same embedding (E7 vs E4/E5/E6/E12T; E11 vs E8/E9/E10/E12B).
- A CI that includes 0 means the data do not distinguish the models.
- Fine-tuned results are a different protocol and must not be ranked against frozen results.
