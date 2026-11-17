# Results interpretation

Automatically derived, intentionally conservative statements (profile `smoke`).

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

## Reading guide

- Prefer recording-level metrics; window-level numbers are correlated within recordings.
- Compare VQC only with heads on the same embedding (E7 vs E4/E5/E6/E12T; E11 vs E8/E9/E10/E12B).
- A CI that includes 0 means the data do not distinguish the models.
- Fine-tuned results are a different protocol and must not be ranked against frozen results.
