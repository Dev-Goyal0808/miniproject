# Results interpretation

Automatically derived, intentionally conservative statements (profile `full`).

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

## Reading guide

- Prefer recording-level metrics; window-level numbers are correlated within recordings.
- Compare VQC only with heads on the same embedding (E7 vs E4/E5/E6/E12T; E11 vs E8/E9/E10/E12B).
- A CI that includes 0 means the data do not distinguish the models.
- Fine-tuned results are a different protocol and must not be ranked against frozen results.
