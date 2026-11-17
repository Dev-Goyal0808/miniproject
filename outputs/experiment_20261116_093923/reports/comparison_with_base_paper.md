# Comparison with the base paper

Base paper: Dash S., Dash D.K., Tripathy R.K., Pachori R.B., *Time-frequency domain machine learning for detection of epilepsy using wearable EEG sensor signals recorded during physical activities*, Biomedical Signal Processing and Control 100 (2025) 107041.

## 1. Comparison table

| Aspect | Base paper | Proposed project |
|---|---|---|
| Input | Wearable FP1 EEG | Same dataset source, FP1, 512 Hz |
| Preprocessing | WOSG | WOSG reproduction (structure published; wavelet/level/SG parameters and optimisation criterion are assumptions) |
| Segmentation | 5 seconds | 5 seconds (2,560 samples), non-overlapping (configurable overlap) |
| TF transform | GWST | GWST (Eq. 1-3), 0.5-50 Hz, 225 voices, exact fractional-k evaluation |
| Handcrafted features | L1 + Shannon entropy | Reproduced 450-D baseline (E1-E3) |
| Feature learning | Existing ML/DL models | Temporal GWST tokens + Transformer and Bi-LSTM (independent) |
| Quantum component | Not used | Six-qubit VQC (E7, E11) + no-CNOT ablation (E12) |
| Classical control | Existing classifiers | Matched linear / MLP / RBF-SVM heads on identical 6-D embeddings |
| Activity evaluation | Published activity protocols | Activity-wise, group-wise and leave-one-activity-out |
| Artifact robustness | Original evaluation | Controlled synthetic corruption (Gaussian, drift, EMG-like, ocular-like; 20/10/5 dB) |
| Prediction level | Reported frame-based evaluation | Window and recording-level (primary) |

## 2. Point-by-point

1. **Same dataset source** - the public wearable-EEG ADL dataset (NeuroSky MindWave 2.0).
2. **Same FP1 single-channel context**; 3. **same 512 Hz** sampling.
4. **WOSG intention** is kept (DWT -> SG on the approximation -> subtraction). Exact parameters are unpublished -> documented assumptions, per-recording SG optimisation by an unsupervised proxy objective.
5. **Five-second segmentation** and 7. **0.5-50 Hz** range are reproduced; 6. **GWST** is implemented from the paper's equations.
8. **L1 + Shannon entropy** baseline: 450-D vectors, RF/SVM and MI-selected RF are reproduced as E1-E3.
9-11. **Additional**: temporal log-GWST tokens, Transformer vs Bi-LSTM encoders, 6-D learned bottleneck.
12-13. **Six-qubit VQC** compared with matched classical heads on identical embeddings.
14. **Activity-held-out robustness**, 15. **synthetic artefact robustness**, 16. **recording-level prediction** are new evaluations.

## 3. Published reference values (quoted from the paper, NOT produced by this code)

| Item | Published value |
|---|---|
| Random Forest, GWST L1+entropy, hold-out validation (70/10/20 frames) | 90.74 % accuracy |
| Multi-layer LSTM, 10-fold CV | 74.44 % average accuracy |
| Multi-layer LSTM, jogging / running / idle sitting activity-specific | 82.72 % / 82.41 % / 87.30 % |

These numbers use the paper's own protocol (frame-based splits) and **cannot be compared directly** with this project's recording-grouped results. Our corresponding values from this run (recording-level, pooled outer CV, balanced accuracy [95% CI]): E1 RF 0.812 [0.630, 0.948]; E2 SVM 0.896 [0.785, 0.992].

## 4. Discrepancies and caveats found while reproducing

- **Recording counts.** The paper text states 60 healthy and 30 epilepsy recordings in the database but also that 30 healthy + 30 epilepsy recordings were used. The archive contains 60 healthy + 30 epilepsy files (this project uses all 90 in the main CV and reports a subset restricted to activities present in both classes).
- **Frame count.** The paper reports 540 frames for 5 s windows (and 3000 / 1440 / 960 / 660 for 1-4 s) with a stated total of 45 minutes. 60 recordings x 20 s = 20 min would give 240 non-overlapping 5 s frames, and the 90 files give 360. The 540 figure therefore cannot be reproduced with non-overlapping windows from the archive; the paper does not state an overlap, so the reason (overlap, different data, counting) is unknown.
- **Window length.** Each CSV has 10,241 rows instead of the documented 10,240 (see dataset audit).
- **Frame-level splitting.** The paper evaluates frames with 70/10/20 hold-out and 10-fold CV and mentions subject-specific selection, but does not state recording-level grouping for the wearable database. If frames from the same recording appear in training and test partitions, accuracy can be inflated by within-recording leakage. This is a possibility to check with the authors, not a verified finding. This project prevents it by construction.
- **Subject independence.** The archive has no participant IDs; neither this project nor (as far as the available description shows) the archive allows verifying participant-independent evaluation.
- **Histogram 'bin size of 10'** and **225 frequency components** are interpreted as 10 bins and 225 voices; WOSG parameters are not given in the paper.
- **Hyper-parameters.** The paper's grid search (Table 1) selects on the validation set; this project also selects on validation recordings only.
