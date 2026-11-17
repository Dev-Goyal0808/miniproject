# Methodology report

Profile: **enhanced**; seeds: [0, 1, 2]; outer folds: 5 (run: all); device: cuda.

## 1. Preprocessing - WOSG (published algorithm vs implementation assumptions)

**Published structure** (Gajbhiye et al., IEEE Trans. Instrum. Meas. 2021, as cited by the base paper): discrete wavelet transform; an optimised Savitzky-Golay (SG) filter is applied to the artefact-contaminated *approximation* sub-band; the SG output (artefact estimate) is subtracted from the approximation; the filtered EEG is the inverse DWT of the cleaned approximation plus the unchanged detail sub-bands.

**Not available to this implementation (neither in the base paper nor in the accessible abstract of the cited paper)**: wavelet family, decomposition level, SG window length, SG polynomial order and the optimisation criterion. Therefore:

- wavelet = `db4`, level = 7 (approximation band 0-2.00 Hz at 512 Hz), mode = `symmetric` (**assumption**);
- SG (window, order) is chosen **per recording** by grid search over windows [5, 9, 13, 17, 21, 31, 41, 51] and orders [1, 2, 3] minimising `J = P_low(clean)/P_low(raw) + 1.0 * (1 - corr_in-band)` (power below 0.5 Hz vs correlation within [0.5, 50.0] Hz). This is an **unsupervised proxy objective of this project - not the criterion of the original paper**;
- the filter is applied to the whole recording before segmentation, as in the base-paper flow chart; a Butterworth filter is NOT used as a substitute.

Observed effect on this dataset: median low-frequency (<0.5 Hz) power ratio raw/filtered = 61.4; chosen (window, order) counts: {'w5_p3': 62, 'w5_p2': 15, 'w9_p3': 9, 'w9_p2': 4}.

## 2. Segmentation

5 s windows at 512 Hz = 2,560 samples, overlap 0% (hop 2560). Recording ID, class, activity and window index are stored for every window (`data/window_metadata.csv`). Windows of one recording are never split across train/validation/test.

## 3. GWST

Implemented from Eq. (1)-(3) of the base paper (standard S-transform with Gaussian window `exp(-2 pi^2 m^2 / k^2)`, periodic/symmetric in m). 225 voices equally spaced in 0.5-50.0 Hz. Since the 0.2 Hz DFT grid does not contain these voices, Z(m+k) is evaluated **exactly** for fractional k via a frequency-shifted DFT (no interpolation). Verified against a direct O(N^2) evaluation of the definition (max abs error 1.58e-15) and by localising a 10 Hz sine at 10.00 Hz. Not STFT, not CWT.
Ambiguity: the paper's 'histogram bin size of 10' is implemented as **10 equal-width bins**; its '225 frequency components' is implemented as 225 equally spaced voices.

## 4. Handcrafted baseline

L1 norm (sum over time of |GWST| per frequency) and Shannon entropy (bits; 10-bin normalised histogram; 0 log 0 := 0) -> 450-D vector (asserted). E1 Random Forest, E2 SVM, E3 mutual-information selection (fitted on the training partition only) + Random Forest. Hyper-parameters (grids in config) are selected by validation log-loss; models are fitted on the training partition only (identical label budget to the neural models).

## 5. Temporal representation and encoders

`log(1 + |GWST|/a0)`, a0 = median over training windows and frequencies of the per-window mean |GWST| (training data only); mean-pooling of 40 consecutive samples -> 64 tokens; per-frequency standardisation with training statistics; Linear(F=225 -> 32). Token tensor per window: [64, 225]; encoder input [B, 64, 32].

- **Transformer**: sinusoidal positional encoding, 2 pre-norm blocks, 4 heads, FF 64, GELU, dropout 0.1, residuals, temporal attention pooling -> [B,32].
- **Bi-LSTM**: 1 layer, 16 hidden units per direction, dropout 0.1, temporal attention pooling -> [B,32].
- **Shared embedding**: LayerNorm(32) -> Linear(32,6) -> Tanh.

Parameter counts:

```json
{
  "n_freq_F": 225,
  "transformer": {
    "total_trainable_encoder_incl_projection_and_embedding": 25734,
    "token_projection": 7232,
    "core_incl_attention_pooling": 18240,
    "embedding_layer": 262
  },
  "bilstm": {
    "total_trainable_encoder_incl_projection_and_embedding": 14982,
    "token_projection": 7232,
    "core_incl_attention_pooling": 7488,
    "embedding_layer": 262
  },
  "heads": {
    "linear(6,1)": 7,
    "mlp(6-6-1)": 49,
    "vqc_6q_2layers_ring": {
      "total": 55,
      "circuit_weights": 36,
      "output_linear(6,1)": 7
    },
    "vqc_no_cnot": {
      "total": 55,
      "circuit_weights": 36,
      "output_linear(6,1)": 7
    }
  },
  "quantum_circuit": {
    "n_qubits": 6,
    "layers": 3,
    "encoding": "RY(pi*z_i)",
    "variational": "RY(theta) RZ(phi) per qubit per layer",
    "entanglement": "CNOT ring 0->1->2->3->4->5->0 after the rotations of each layer",
    "measurement": "<Z_i> for i=0..5 -> Linear(6,1)",
    "simulator": "default.qubit",
    "diff_method": "backprop"
  }
}
```

## 6. Heads on the SAME 6-D embedding

Linear(6,1); MLP 6-6-1 (Tanh); RBF-SVM (C, gamma chosen on validation log-loss); six-qubit VQC (PennyLane `default.qubit`, torch interface, backprop): |0>^6 -> RY(pi z_i) -> 2 x [RY, RZ on every qubit -> CNOT ring 0->1->2->3->4->5->0] -> <Z_i> -> Linear(6,1). Interpretation of the specification: the CNOT ring is applied after the rotations **inside each variational layer**. E12 removes the CNOT ring only.
Gradient check (Transformer and Bi-LSTM): all gradient norms non-zero = **True** (`config/gradient_check.json`).

**Frozen-encoder protocol (primary).** For every (seed, fold) each encoder is first trained end-to-end with a mlp head (BCE-with-logits, AdamW, early stopping on validation loss) to produce the embedding; the encoder is then frozen and all heads are trained/fitted on the identical embeddings of the identical training windows. **Caveat:** the embedding was optimised for the pre-training head (`model.encoder_pretrain_head` = mlp), which can favour that head type in the frozen comparison. The separate **end-to-end fine-tuning** comparison (FT-*) starts from the same pre-trained encoder and trains each head jointly; it is reported in its own table and is never mixed with frozen results.

## 7. Training configuration

```json
{
  "batch_size": 16,
  "optimizer": "AdamW",
  "weight_decay": 0.001,
  "lr_encoder": 0.001,
  "lr_head": 0.01,
  "lr_quantum": 0.01,
  "lr_finetune_encoder": 5e-05,
  "encoder_lr_grid": [
    0.0003,
    0.001
  ],
  "head_lr_grid": [
    0.001,
    0.003,
    0.01,
    0.03
  ],
  "max_epochs": 120,
  "patience": 20,
  "head_max_epochs": 160,
  "head_patience": 25,
  "ft_max_epochs": 120,
  "ft_patience": 20,
  "grad_clip": 1.0,
  "use_class_weights": true,
  "min_delta": 1e-05,
  "mixup_alpha": 0.15
}
```

No hyper-parameter search is run on neural models unless `train.encoder_lr_grid` / `train.head_lr_grid` are set; validation-based grids exist only for the sklearn models (see config). This asymmetry (grid-tuned SVM/RF vs fixed-lr networks) is a limitation of the comparison.

## 8. Data splitting and leakage control

Outer: 5-fold `StratifiedGroupKFold` over windows with **recording** as the group (shuffled with the experiment seed). Inner: a recording-level validation partition (1/4 of the training recordings) for early stopping, model selection and thresholds. Test recordings are used only for evaluation. Fold assignments: `config/fold_assignments.csv`. If a valid grouped stratified split cannot be built the run stops. **No participant IDs exist**: splits are recording-level, multiple recordings may come from the same person, so no participant-independent generalisation is claimed.

## 9. Recording-level prediction

Window probabilities are averaged per recording; the recording-level threshold maximises balanced accuracy on **validation recordings only** (ties -> closest to 0.5; falls back to 0.5 if validation has one class). A separate window-level threshold is selected on validation windows. Recording-level metrics are primary.

## 10. Activity and noise robustness

Activity-wise / group metrics come from pooled outer-CV test predictions. Leave-one-activity-out trains on the other eligible activities (complete recordings, validation partition drawn from them) and tests on the held-out activity (eligible activities: desk work, idle sitting, jogging, laying, running, sitting, stairs, walking).
Noise: synthetic corruption of **test recordings only** before the (identical) WOSG/GWST pipeline; trained models, normalisation and thresholds are unchanged. SNR reference: variance of the raw recording; deterministic generators seeded by (noise seed, recording, type, SNR). **This is a controlled robustness experiment with synthetic signals; it does not show performance under real motion, EMG or ocular artefacts, and the synthetic EMG/ocular-like signals are not recorded artefacts.**

## 11. Statistics

Bootstrap (%d replicates, %.0f%% percentile CI) resamples **complete recordings** (the same resample for all seeds, metrics averaged over seeds). Paired differences between models use the same resamples; exact McNemar tests are reported per seed. No multiplicity correction is applied: all comparisons are exploratory. Fold-level mean +/- std use (seed, fold) pairs, which are not independent samples.

## 12. Self-tests

```json
{
  "gwst_vs_direct_definition_max_abs_error": 1.5803626013929105e-15,
  "gwst_peak_frequency_of_10Hz_sine": 10.002232142857142,
  "wosg_lowfreq_power_reduction_factor": 273.0542492786233,
  "wosg_10Hz_amplitude_ratio": 0.9959135954595296,
  "entropy_uniform_bits": 3.321928094887362,
  "entropy_constant_bits": -0.0,
  "segmentation_10241_samples": {
    "windows": 4,
    "leftover": 1
  },
  "token_shape": [
    2,
    64,
    225
  ],
  "all_passed": true
}
```
