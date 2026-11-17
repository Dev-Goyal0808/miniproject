# Hybrid Quantum Classical EEG Classification

40 page report draft | 17 November 2026



<!-- PDF page 1 -->

## Hybrid Quantum Classical EEG Classification

A critical study of saved experimental results and the role of variational quantum classifiers

MINI PROJECT REPORT DRAFT
Prepared for academic review | 17 November 2026

This report examines a wearable EEG classification pipeline combining wavelet based artefact filtering, a Gaussian window Stockwell transform, temporal neural encoders and a six qubit variational quantum classifier. It analyses the experimental files already present in the project repository. No model was trained, fine tuned or evaluated on newly generated predictions during report preparation.

The principal conclusion is that the saved quantum models demonstrate feasible integration and useful discrimination, but do not establish quantum advantage. Strong classical controls usually achieve higher point estimates. The strongest defence is therefore a controlled investigation of the quantum component, including unfavourable comparisons, rather than a claim that quantum classification must outperform classical learning.

The evidence also requires a qualification beyond model accuracy. Three healthy recordings have identical signal hashes and cross split boundaries. The existing results remain descriptive outputs of the recorded protocol; they are not a clean estimate of performance on independent patients or independent signal content.

The report contains the methodology, numerical results, uncertainty analysis, augmentation audit, literature based interpretation and a viva defence. Names, institution details and supervisor declarations have deliberately not been invented. These may be added to a college cover sheet before submission.


<!-- PDF page 2 -->

## Abstract

Wearable EEG classification is difficult because recordings are short, activities alter signal characteristics and a dry electrode is vulnerable to movement related contamination. A hybrid quantum classical architecture provides a way to test whether a parameterised quantum decision head contributes beyond a classical representation. The present work critically reviews saved outputs from such a pipeline, without conducting additional training.

The archived dataset audit identifies 90 recordings comprising 60 healthy and 30 epilepsy labelled files sampled at 512 Hz. Five second segmentation produces 360 non overlapping windows. A wavelet domain filtering procedure precedes the Gaussian window Stockwell transform. Handcrafted features provide classical baselines, while Transformer and bidirectional LSTM encoders produce six dimensional embeddings for matched linear, multilayer perceptron, RBF SVM and variational quantum heads. The selected complete enhanced experiment uses three seeds and five recording grouped outer folds [P1].

Transformer plus VQC achieves 81.11% recording accuracy, 78.61% balanced accuracy and 0.8919 ROC AUC. Transformer plus MLP achieves 83.70%, 81.39% and 0.9022 respectively. The paired balanced accuracy difference for VQC minus MLP is minus 2.78 percentage points, with an archived 95% interval spanning minus 6.82 to plus 1.80 points. This interval does not establish equivalence. Removal of CNOT gates improves the Transformer VQC point estimate to 81.11% balanced accuracy, weakening any claim that entanglement explains the performance.

A separate waveform augmentation archive improves Bi LSTM VQC balanced accuracy from 77.50% to 82.50% within that experiment [P2]. A quick MixUp comparison produces identical metric files and cannot demonstrate an augmentation benefit [P3]. Duplicate signal content crossing partitions, unavailable participant identifiers, class dependent activity coverage and small sample size limit all generalisation claims.

The defensible contribution is a transparent benchmark showing where a compact simulated quantum head succeeds, where classical models remain stronger and which design hypotheses require future tests. Neither hardware noise, computational speedup nor clinical readiness is demonstrated. Keywords: wearable EEG; Stockwell transform; VQC; matched baselines; balanced accuracy; reproducibility.


<!-- PDF page 3 -->

## Contents and Reading Guide

Pages 4 to 7 establish the research question, related work and evidence provenance. Pages 8 to 17 explain the dataset, signal processing, neural and quantum architecture, evaluation protocol and statistical interpretation. Pages 18 to 29 analyse the saved results. Pages 30 to 36 develop the quantum defence, limitations and conclusions. Pages 37 and 38 contain references; pages 39 and 40 provide an evidence register and submission guidance.

All numerical percentages describe this repository unless explicitly labelled as a published result. Percentage point differences are absolute differences between percentages. ROC AUC, MCC and probabilities retain their unitless scales. The term epilepsy labelled recording refers to the archive class, not a verified seizure event within every window.

The report uses numbered literature citations [1] to [12] and project evidence identifiers [P1] to [P6]. The source register resolves project identifiers to repository paths. Tables are transcribed or calculated from saved CSV values. Charts redraw saved values and do not contain new model predictions.

Readers preparing an oral defence should begin with pages 18, 19, 21, 27, 28, 31 and 33. Those pages contain the main result, a fair Transformer comparison, the entanglement ablation, the augmentation distinction and concise answers to likely objections.


| Topic | Pages |
| --- | --- |
| Problem and related work | 4-7 |
| Dataset and signal processing | 8-12 |
| Architecture and protocol | 13-17 |
| Results and sensitivity analyses | 18-29 |
| Quantum interpretation and defence | 30-33 |
| Limitations and conclusions | 34-36 |
| References and evidence register | 37-40 |


<!-- PDF page 4 -->

## Research Problem and Study Objectives

The implemented task is binary classification of healthy versus epilepsy labelled wearable EEG recordings obtained during activities of daily living. Its output is a recording label formed by aggregating window probabilities. It does not estimate seizure onset time, predict a future seizure or diagnose an individual patient independently of the dataset labels. These distinctions matter because an impressive recording accuracy cannot be converted into an event detection sensitivity or false alarms per hour.

The research question is whether a six qubit variational quantum head adds useful predictive behaviour after a learned temporal representation, under the same recording partitions and input dimensions as classical alternatives. A second question concerns the representation itself: whether temporal GWST tokens and attention based pooling are more useful than a fixed set of frequency summaries. A third question asks whether any apparent benefit survives changes in activity, synthetic corruption and augmentation.

The project separates these questions through several controls. RF and SVM baselines use 450 handcrafted features. Transformer and Bi LSTM encoders are tested independently. Frozen embeddings allow linear, MLP, RBF SVM and VQC heads to consume the same six coordinates. An otherwise similar circuit without CNOT gates checks whether the entangling structure improves the result. End to end fine tuning is reported separately because it also changes the representation.

Success must be defined before choosing a preferred result. Integration success means a trainable circuit can participate in the pipeline. Predictive benefit means an improvement on a prespecified metric under a fair comparison. Quantum advantage requires substantially more evidence about classical alternatives and computational resources. The saved files support the first outcome and an informative comparison for the second, but do not establish the third [P1].

This report treats lower quantum accuracy as a finding to explain and delimit. It does not redefine success after seeing the outcome or assume that an emerging method deserves deployment simply because it is quantum.


<!-- PDF page 5 -->

## Wearable EEG and the Classical Research Context

The direct methodological reference is Dash and colleagues [1], which studies wearable EEG recorded during physical activities. Its pipeline applies time frequency processing, extracts L1 norm and Shannon entropy features and evaluates classical and deep models. The supplied paper reports 90.74% RF accuracy in its hold out protocol. That published number is contextual evidence; it is not a measurement generated by this project and is not directly comparable with recording grouped cross validation here.

Earlier supplied EEG studies motivate analysis of nonstationary and nonlinear structure. Sharma and Pachori [9] extract phase space features from intrinsic mode functions, while Sharma, Pachori and Acharya [10] examine entropy measures for focal EEG identification. Bhattacharyya and colleagues [11] use tunable Q wavelet decomposition with multiscale entropy. These works support the general choice to analyse frequency structure and complexity, but their labels and recording conditions differ from the wearable classification task.

Bhattacharyya and Pachori [12] examine patient specific multivariate seizure detection using empirical wavelets. This is a different problem from classifying single channel wearable recordings. Its multichannel, event oriented setting prevents using its reported accuracy as a target that the present method must match. Differences in label definition, subject access, channel count and validation unit are at least as important as the classifier name.

Two other supplied resources address pediatric sleep and EEG air writing. They were inspected for scope but are not used as epilepsy performance baselines. A sleep corpus cannot validate seizure classification, and improvement in air writing recognition does not demonstrate an epilepsy benefit. The two local copies of the Dash paper represent one reference, not two independent studies.

The resulting literature position is specific: this project extends a wearable time frequency pipeline with learned temporal embeddings and controlled quantum heads. It does not claim a first use of EEG machine learning, a reproduction of every published protocol or a general superiority over unrelated biomedical classifiers.

The reference publication reports 540 five second frames and 45 minutes for its wearable analysis, while the archived 90 files yield 360 non overlapping frames and approximately 30 minutes. These counts cannot be reconciled from the supplied archive alone. Overlap, a different source subset or another counting convention may explain the difference, but none is verified. Recording grouping is not explicit in the published frame based protocol. This is a reason to avoid a direct 90.74% versus 80.37% RF leaderboard comparison, not proof of leakage in the published study.


<!-- PDF page 6 -->

## What Quantum Literature Can Actually Defend

Bowles, Ahmed and Schuld [2] benchmark quantum models against classical controls and report that conventional classifiers often perform better. Their study also finds cases where removing entanglement preserves or improves performance. It supplies a directly relevant precedent for reporting unfavourable quantum comparisons as useful evidence about model design. It does not prove that this EEG model is optimal or that its observed gap is harmless.

Schuld and colleagues [3] present a circuit centric classifier and discuss compact parameterisation under their architecture. Their amplitude encoding setup differs from the angle encoded EEG head. The appropriate lesson is to measure resources alongside prediction quality. A parameter efficiency claim must be established for the actual model and matched baseline; it cannot be borrowed from a different circuit.

Huang and colleagues [4] show that available data can make classical methods competitive and that useful quantum separation depends on problem structure. Their work discourages the assumption that a difficult to simulate feature map automatically supplies a learning advantage. Caro and colleagues [5] provide generalisation bounds related to trainable gates and sample size under stated assumptions. Such bounds motivate compact models but do not certify this small dataset or the complete hybrid encoder.

Encoding and trainability offer further context. Schuld, Sweke and Meyer [6] connect accessible function spectra to encoding choices. Perez Salinas and colleagues [7] study repeated data encoding. McClean and colleagues [8] identify barren plateaus for classes of parameterised circuits. These papers suggest hypotheses to investigate; they do not diagnose the cause of this experiment's lower accuracy.

The literature therefore supports a disciplined defence: the quantum head is a testable inductive bias, classical superiority is plausible and a transparent negative or mixed result has scientific value. The report keeps this argument separate from unsupported promises about future hardware.


<!-- PDF page 7 -->

## Evidence Selection and Experiment Provenance

Several experiment folders exist and should not be pooled as though they were independent replications. The main detailed analysis uses experiment_20261116_143634 because it includes a complete final report, configuration, recording metrics, paired comparisons and activity and noise results [P1]. It is an enhanced configuration with seeds 0, 1 and 2 and five outer folds. This choice is based on completeness and analytical scope, not on selecting the highest quantum score.

The earlier full run, experiment_20261116_095358, is retained as an architecture sensitivity check [P4]. Smoke and quick runs are development evidence. They use smaller budgets and should not carry the headline accuracy. A later archive, experiment_20261116_202913, contains 38 model rows covering baseline and waveform augmented models, plus augmentation audit files [P2]. Its final report is absent. Its metrics are still usable as saved secondary evidence, but the archive is not described as fully documented.

The quick augmentation study under outputs_gwst_vqc_ablation uses a different setup and one seed [P3]. Its intended MixUp intervention is assessed independently from waveform augmentation. Mixing these studies would combine different scripts, hyperparameters and computational budgets and would obscure the actual treatment.

All findings in this report come from reading existing artifacts or calculating summaries from them. Hash comparisons, duplicate partition checks, plotting and document generation do not retrain any model. The dataset itself was not present for independent reconstruction of raw waveforms. The archived manifest and reports establish what the previous run recorded, with the limitations described throughout this report.

The repository revision inspected is 75b5971. The saved run environments use Python 3.10 and PennyLane 0.42.3. The newly installed workspace environment is different and was not used to generate the experimental scores. Its successful startup checks are not a reproduction of the historical results.


| Evidence | Role |
| --- | --- |
| P1 Enhanced complete run | Primary detailed analysis |
| P2 Waveform augmentation archive | Secondary within run comparison |
| P3 Quick MixUp pair | Intervention validity audit |
| P4 Earlier full run | Architecture sensitivity |


<!-- PDF page 8 -->

## Dataset Inventory and Activity Imbalance

The archived audit contains 90 wearable EEG files: 60 healthy and 30 epilepsy labelled recordings. Every file has 10,241 numeric samples rather than the documented 10,240. At 512 Hz the nominal duration is approximately 20 seconds. Filtering all samples and retaining complete five second windows yields four windows per file, 360 windows in total and one unused sample per file [P1].

The class distribution gives a majority classifier 66.67% accuracy while its balanced accuracy is 50%. This simple reference explains why accuracy alone is inadequate. A model can improve its total accuracy by favouring the healthy class and still miss many epilepsy labelled recordings. Sensitivity, specificity and balanced accuracy therefore accompany all primary claims.

Activity coverage is also asymmetric. Cooking, jumping, standing and watching television contain only healthy recordings. The remaining eight activities contain both classes. The healthy only activities account for 13 recordings, leaving 77 recordings in the paired activity subset. A classifier may exploit activity correlated information, so the all activity result is not a pure measurement of epilepsy related physiology.

Participant identifiers are unavailable. Recording counters in file names are not subject identifiers. Consequently the number of unique people, the presence of repeated individuals across partitions and the effective number of independent participants cannot be determined. Ninety recordings must never be described as ninety patients.

The audit also flags quantisation and possible clipping. These observations indicate signal quality constraints but do not by themselves establish a hardware failure or its effect on a specific classifier. The report uses the manifest as an inventory of the archived experiment, rather than as a substitute for a clinically curated dataset.


| Quantity | Saved value |
| --- | --- |
| Healthy recordings | 60 |
| Epilepsy labelled recordings | 30 |
| Total recordings and windows | 90 and 360 |
| Nominal sampling rate | 512 Hz |
| Shared activities | 8 |
| Healthy only activities | 4 |
| Participant identifiers | Unavailable |


<!-- PDF page 9 -->

## Duplicate Signals and Independence of the Splits

A read only audit of dataset_manifest.csv groups recordings by the archived SHA1 signal hash. H_00_idle_sitting1, H_00_idle_sitting2 and H_00_idle_sitting3 share the same hash. The manifest therefore identifies one group of three identical signal contents. With all other hashes distinct, 90 files represent 88 distinct hashed signal sequences. This is not a count of distinct people [P1, P5].

Joining these identifiers to fold_assignments.csv reveals cross partition placement in 14 of the 15 seed and fold combinations. In nine combinations, the duplicate group includes both training and test recordings. Some combinations also place a duplicate in validation. This confirms that grouping only by file or recording identifier did not prevent all identical content leakage.

The consequence is precise. Windows from a single recording identifier are kept together, but identical waveforms under different identifiers can still occur on opposite sides of a split. All models share this limitation; it does not prove that one classifier received a unique advantage. It does make independence claims and uncertainty estimates more optimistic than a strictly content independent evaluation would justify.

The report retains the saved scores because retraining was explicitly excluded. It does not relabel them as corrected results or subtract an assumed amount of inflation. Removing duplicate test rows after training would not remove contamination from fitting or validation and would not produce a clean retraining free estimate.

A future correction should combine identical hashes into a common group before any splitting, or remove duplicate contents according to a documented rule. Subject identifiers would still be needed for patient independent evaluation. This limitation should be disclosed during the viva before an examiner discovers it; acknowledging a verified boundary is a stronger defence than claiming the protocol is entirely leakage free.


| Check | Finding |
| --- | --- |
| Identical hash group | Three healthy idle sitting files |
| Distinct hashed contents | 88 |
| Cross partition combinations | 14 of 15 |
| Train and test overlap combinations | 9 of 15 |
| Numerical correction attempted | None |


<!-- PDF page 10 -->

## Wavelet Domain Artefact Filtering

The filtering implementation follows the broad WOSG structure described in the project methodology and motivated by the reference paper. A discrete wavelet transform separates the recording into approximation and detail bands. Savitzky Golay smoothing estimates a low frequency artefact contribution in the approximation band. Subtracting that estimate and reconstructing the signal leaves the detail bands unchanged [1, P1].

The project uses the db4 wavelet, seven levels and symmetric boundary handling. At 512 Hz the level seven approximation primarily covers the lowest frequencies. Candidate SG windows and polynomial orders are selected per recording using an unsupervised proxy objective involving residual low frequency power and preservation of in band correlation. This is a project implementation choice. It is not a verified reconstruction of every parameter in the original WOSG study.

The archived methodology reports a median raw to filtered low frequency power ratio of approximately 61.4. This suggests substantial suppression of the targeted component, but a large ratio does not prove that all removed content was artefact. Low frequency neural information can also be affected. A filter should be judged jointly by signal preservation, task relevance and validation performance.

Filtering the entire recording before non overlapping segmentation avoids an artificial boundary at each five second window. It also means the current preprocessing is offline. Samples later in a recording can influence a reconstructed earlier sample, so a real time application would require a causal design or an explicitly measured buffering delay.

The distinction between signal based parameter adaptation and label based model selection is important. The per recording filter search does not use class labels. Nonetheless, its exact choices, boundary effects and assumptions should be documented, especially when comparing with a published baseline. Replacing it silently with a different filter would alter the experimental question.


<!-- PDF page 11 -->

## Gaussian Window Stockwell Representation

The Gaussian window Stockwell transform supplies a localised time frequency representation rather than a single spectrum for a complete recording. For this implementation, each five second window contains 2,560 samples. The transform evaluates 225 frequencies from 0.5 to 50 Hz, producing a frequency by time matrix from which both summary features and temporal tokens are derived [P1].

The transform uses frequency dependent Gaussian localisation. Lower frequencies receive broader time support while higher frequencies are more localised. This design is relevant for EEG because oscillatory content can vary within a recording. It does not guarantee separation of healthy and epilepsy classes; its usefulness is an empirical question addressed through downstream models.

Five seconds at 512 Hz gives a DFT spacing of 0.2 Hz. The chosen 225 voices do not all fall on that grid. The archived implementation evaluates fractional frequency shifts through a shifted DFT rather than silently snapping all voices to bins. Its saved self test compares integer frequency cases against a direct definition and reports a maximum absolute discrepancy of approximately 1.58 times 10 to the power minus 15. A synthetic 10 Hz sinusoid is localised near 10.00 Hz.

These numerical checks support internal consistency of the transform routine. They do not validate the clinical labels, prove artefact removal or establish equivalence with every implementation choice in the reference publication. Numerical correctness and clinical validity answer different questions.

The shared transform also helps experimental control: handcrafted and learned branches begin with the same filtered signal representation. A strong learned result therefore reflects the combination of representation and classifier, while a head comparison on frozen embeddings isolates a narrower question about the decision function. This hierarchy should remain visible in the report's conclusions.

In continuous notation, S(tau,f) = integral x(t) g(t-tau,f) exp(-j 2 pi f t) dt, where g(u,f) = |f| exp(-f squared u squared / 2) / sqrt(2 pi). The Gaussian width changes with frequency. The discrete implementation evaluates the corresponding shifted spectrum with its Gaussian frequency kernel. The reported branch uses the magnitude |S|, so it does not retain the complete phase information in the classifier input.


<!-- PDF page 12 -->

## Handcrafted Features and Classical Baselines

For each of the 225 frequency rows, the handcrafted branch computes an L1 magnitude summary and Shannon entropy of a normalised histogram. Concatenation yields a 450 dimensional feature vector. Entropy uses ten equal width bins as the project's interpretation of the reference description. The implementation defines the zero probability contribution as zero [P1].

E1 fits a random forest, E2 an SVM and E3 mutual information selected features followed by a random forest. Feature selection and scaling are fitted within the training partition. Validation loss chooses hyperparameters from the saved grids. This matters because choosing features with labels from the complete dataset would leak test information even if the classifier itself were fitted only on training rows.

The enhanced run records 80.37% RF accuracy and 76.11% balanced accuracy. SVM accuracy is 82.22%, but sensitivity is only 58.89%, against specificity of 93.89%. Thus the higher SVM accuracy accompanies poorer recall of epilepsy labelled recordings. Mutual information plus RF yields 75.93% accuracy and 71.67% balanced accuracy, showing that feature reduction did not automatically improve this small dataset.

These models are useful deployment oriented references because they avoid a trainable temporal encoder and quantum simulation. Their input dimension differs from the six dimensional neural embeddings, so comparisons against VQC describe complete pipelines rather than isolated head efficiency. Linear and MLP heads on the same frozen embeddings provide the more direct classifier control.

The saved hyperparameter grids are finite and no claim of an exhaustive classical search is made. Conversely, quantum models should not be excused by assuming that only they suffer from tuning limitations. Both families operate under the recorded protocol and its shared data weaknesses.

For frequency row f, L1(f) = sum over time of |S(f,t)|. Entropy is H(f) = -sum over bins b of p(b) log2 p(b), with zero probability contributions defined as zero. The feature vector concatenates these two 225 value sequences. These summaries discard temporal order; the token branch retains a coarse sequence and asks whether learning from that sequence is useful.


| Model | Accuracy % | Balanced % | Sensitivity % |
| --- | --- | --- | --- |
| E1 | 80.37 | 76.11 | 63.33 |
| E2 | 82.22 | 76.39 | 58.89 |
| E3 | 75.93 | 71.67 | 58.89 |


<!-- PDF page 13 -->

## Temporal Encoders and the Shared Bottleneck

The temporal branch converts GWST magnitudes to log(1 plus magnitude divided by a training derived scale). Mean pooling over 40 time samples produces 64 temporal tokens, each containing 225 frequency values. Standardisation uses training statistics. A linear projection maps each token to 32 coordinates before temporal encoding [P1].

The Transformer has two blocks, four attention heads and a feedforward width of 64. The enhanced configuration specifies dropout 0.2. A separate bidirectional LSTM has 16 hidden units in each direction. Temporal attention pooling summarises either encoder to 32 values. Layer normalisation, a linear projection and a tanh activation produce the shared six dimensional bottleneck.

The archived parameter inventory gives 25,734 parameters for the Transformer encoder and 14,982 for the Bi LSTM encoder, including projection and embedding layers. These are substantial classical models relative to a seven parameter linear head or a 55 parameter quantum head. Describing the whole hybrid as a tiny quantum model would conceal where most learning capacity resides.

Encoder pretraining uses a classical MLP head. Frozen comparisons then reuse the same learned coordinates for all heads of a given encoder, fold and seed. This is a valuable fairness control because VQC does not receive more input features. It also introduces a limitation: the representation was optimised with a classical pretraining objective, not specifically for the quantum function family.

That limitation is an explanatory hypothesis, not proof that quantum results would improve with another embedding. End to end fine tuning partly addresses adaptation, but it is a different experiment because each head can change the encoder. The report therefore keeps frozen head and fine tuned results separate.


| Stage | Output shape for one window |
| --- | --- |
| GWST magnitudes | 225 frequencies by 2560 samples |
| Pooling and standardisation | 64 tokens by 225 features |
| Token projection | 64 tokens by 32 features |
| Attention pooled representation | 32 values |
| Shared bottleneck | 6 bounded values |


<!-- PDF page 14 -->

## Six Qubit Variational Quantum Classifier

The enhanced VQC operates on the six dimensional bottleneck. Its implemented forward pass first applies a trainable per coordinate scale and bias and another tanh calibration, then converts the calibrated values to rotation angles. Six RY encoding gates prepare an input dependent state from the all zero state. Three variational layers apply an RY and RZ rotation on every qubit, followed by a six edge circular CNOT pattern [P1].

The circuit measures six Pauli Z expectation values. A classical linear layer maps those expectations to one logit, from which the probability is obtained. PennyLane default.qubit performs statevector simulation with backpropagation. There is no physical quantum processor, explicit hardware noise channel or finite shot sampling in the saved configuration.

Parameter accounting requires care. Three layers times six qubits times two rotations gives 36 variational rotation parameters. Input calibration contributes 12 and the final linear readout contributes seven. The archived total of 55 parameters is therefore consistent with the code. Some generated text labels still mention two layers or fixed input angles, and the inventory dictionary key contains 2layers. The saved configuration, actual tensor counts and current implementation support three layers with calibration. The prose labels should not override those artifacts.

Removing CNOT gates defines E12T and E12B. These retain quantum rotations and readout but eliminate the entangling structure. They test the effect of the circuit topology under the recorded setup; they do not establish a useful quantum resource advantage.

A six qubit pure state has 64 complex amplitudes. This is small enough for classical simulation, and the Hilbert space size is not the number of independently accessible features or trainable parameters. Its existence alone does not prove a richer useful decision boundary than the classical controls.

The measured feature is q_i(z) = expectation of Z_i in U(z,theta)|0...0>. The readout probability is sigmoid(w dot q(z) + b). The input z originates from a classical encoder, and both angle calibration and readout are classical trainable operations. This explicit separation prevents assigning all representational learning to the quantum state.


| Component | Trainable parameters |
| --- | --- |
| Variational RY and RZ rotations | 36 |
| Input scale and bias | 12 |
| Linear readout | 7 |
| Total VQC head | 55 |
| Matched MLP head | 49 |
| Matched linear head | 7 |


<!-- PDF page 15 -->

## Training and Validation Protocol

The enhanced experiment uses five outer recording grouped folds repeated for seeds 0, 1 and 2. A validation partition is drawn within the outer training portion. Windows belonging to a recording identifier stay together across train, validation and test roles. Hyperparameter selection, early stopping, standardisation and threshold selection use training or validation recordings, not outer test labels [P1].

For a typical fold with 18 test recordings, the remaining 72 recordings are divided again for training and validation. The exact assignments are saved rather than inferred from window indices. Class weighted learning addresses the 60 to 30 class imbalance. The selected configuration includes AdamW, early stopping, gradient clipping and finite learning rate grids.

The maximum budgets are 120 encoder epochs, 160 head epochs and 120 fine tuning epochs, with separate patience values. A maximum is not the number of epochs actually run. Training_summary.csv records selected fit metadata, including elapsed seconds and best validation loss. These files should be used when describing computational effort instead of multiplying maximum epochs by every model.

Frozen head training uses fixed embeddings after encoder pretraining. Fine tuned models update the representation under a selected head. Validation recording probabilities choose a decision threshold. Test recording probabilities are computed as the mean of their four window probabilities, then compared with that fixed threshold.

Two qualifications are necessary. First, windows are correlated observations, so 360 windows do not provide 360 independent people. Second, grouping by recording identifier failed to group the identical hash contents described on page 9. The protocol prevents ordinary within recording window leakage, but it does not guarantee independent content or independent subjects. This distinction is retained even where generated project reports use stronger wording.


<!-- PDF page 16 -->

## Performance Measures and the Decision Threshold

Accuracy is the proportion of correctly classified recordings. Sensitivity is the fraction of epilepsy labelled recordings classified as positive, while specificity is the fraction of healthy recordings classified as negative. Balanced accuracy is their arithmetic mean. In this dataset it gives each class equal influence even though healthy recordings are twice as numerous [P1].

Precision asks how many predicted positive recordings are actually positive. F1 combines precision and sensitivity, while macro F1 averages class specific F1 scores. MCC summarises the four entries of the confusion matrix on a scale from minus one to plus one. No one metric is sufficient to describe all clinically relevant errors.

ROC AUC evaluates score ranking across thresholds, not the chosen binary operating point. A reasonably high AUC can coexist with lower accuracy if probability calibration or a selected threshold produces an unfavourable error tradeoff. PR AUC is sensitive to prevalence and should be interpreted with the 30 of 90 positive class fraction in mind.

The Transformer VQC illustrates this distinction. Its ROC AUC is 0.8919, close to the MLP value of 0.9022, while their balanced accuracies are 78.61% and 81.39%. The scores retain discrimination, but the saved operating point does not recover the best classical performance. This does not prove that another threshold will solve the problem; that threshold would need to be chosen without test label tuning.

A hypothetical always healthy classifier obtains 66.67% accuracy, zero sensitivity and 50% balanced accuracy. This calculation is a reference based on class counts, not a newly trained model. It demonstrates why a defence built only around accuracy would miss the actual value and weakness of the saved predictions.

Using true positive TP, true negative TN, false positive FP and false negative FN counts: accuracy = (TP+TN)/(TP+TN+FP+FN); sensitivity = TP/(TP+FN); specificity = TN/(TN+FP); balanced accuracy = (sensitivity+specificity)/2. Recording probabilities are the mean of four window probabilities. Each seed is scored on its held out recordings before the reported seed average is taken.


| Metric | Question answered |
| --- | --- |
| Accuracy | How often is the recording label correct? |
| Balanced accuracy | How well are both classes recognised? |
| Sensitivity | How many positive recordings are detected? |
| Specificity | How many healthy recordings are rejected? |
| ROC AUC | How well do scores rank the classes? |
| MCC | How strong is the binary association? |


<!-- PDF page 17 -->

## Uncertainty and Paired Statistical Comparisons

The primary recording_metrics.csv pools held out recordings within each seed and then summarises seed level metrics. Bootstrap intervals resample recordings while applying the same resample across models and seeds. The paired comparison table reports model A minus model B, which is more informative about their difference than comparing two separate confidence intervals [P1].

For Transformer VQC minus MLP, the balanced accuracy difference is minus 2.78 percentage points. The archived paired interval includes zero. This means the stored analysis does not resolve the direction with conventional confidence; it does not establish equal performance, noninferiority or clinical interchangeability. Equivalence would require a justified margin and a dedicated analysis established independently of the observed difference.

The output also contains exact McNemar tests by seed. These use discordant correct and incorrect predictions and address a binary accuracy comparison. They do not directly test balanced accuracy differences. Several exploratory model comparisons are reported without multiplicity correction, so isolated nominal significance must be treated cautiously.

Fifteen seed and fold scores are not fifteen independent datasets. Folds share training observations and the same recordings recur across seeds. Seed repetition quantifies some optimisation and partition sensitivity; it does not create new patients. Fold standard deviation should not be described as a confidence interval or divided by the square root of fifteen without considering dependence.

Finally, bootstrap resampling assumes an appropriate observational unit. Duplicate contents and unknown participant clustering challenge the recording independence assumption. The intervals in this report are the saved intervals under the archived method, not fully validated uncertainty bounds for a target patient population. Statistical transparency requires stating both the calculation and the assumptions it cannot verify.

For scale, the saved individual balanced accuracy intervals are 71.95% to 85.65% for Transformer VQC and 73.89% to 88.17% for Transformer MLP. Their overlap is not a comparison test. The paired difference interval, minus 6.82 to plus 1.80 percentage points, is the relevant saved contrast.


| Statement | Supported interpretation |
| --- | --- |
| Interval includes zero | Direction remains uncertain |
| No significant difference | Not proof of equivalence |
| Three seeds | Repeated use of the same dataset |
| Recording bootstrap | Conditional on recording unit assumptions |


<!-- PDF page 18 -->

## Primary Recording Level Results

Table 1 summarises frozen encoder heads and handcrafted baselines from the complete enhanced experiment. Values are pooled recording level metrics averaged over three seeds. Accuracy and balanced accuracy are percentages. The quantum rows are E7 and E11; E12T and E12B remove CNOT gates. Every neural head comparison is tied to its encoder family [P1].

Transformer linear and MLP heads share the highest frozen balanced accuracy point estimate at 81.39%. The MLP gives the highest frozen accuracy at 83.70%. Transformer VQC gives 81.11% accuracy and 78.61% balanced accuracy. These values demonstrate a functioning classifier, but the strongest classical controls remain ahead.

Bi LSTM VQC gives 75.93% accuracy and 75.56% balanced accuracy. Its sensitivity equals the Bi LSTM linear head at 74.44%, but its specificity is lower. The table also shows why a single comparison with the handcrafted baseline would be misleading: Transformer VQC has higher balanced accuracy than RF, while the matched Transformer MLP is stronger still.

These results should be described as the archived performance of this protocol. The duplicate and participant limitations apply to the entire table. Selecting a preferred row does not remove them.


| ID | Accuracy % | Balanced % | Sensitivity % | Specificity % | AUC |
| --- | --- | --- | --- | --- | --- |
| E1 | 80.37 | 76.11 | 63.33 | 88.89 | 0.8772 |
| E2 | 82.22 | 76.39 | 58.89 | 93.89 | 0.8902 |
| E3 | 75.93 | 71.67 | 58.89 | 84.44 | 0.8480 |
| E4 | 83.33 | 81.39 | 75.56 | 87.22 | 0.9002 |
| E5 | 83.70 | 81.39 | 74.44 | 88.33 | 0.9022 |
| E6 | 81.85 | 78.06 | 66.67 | 89.44 | 0.8967 |
| E7 | 81.11 | 78.61 | 71.11 | 86.11 | 0.8919 |
| E8 | 81.11 | 79.44 | 74.44 | 84.44 | 0.9017 |
| E9 | 79.63 | 77.50 | 71.11 | 83.89 | 0.9026 |
| E10 | 80.37 | 78.33 | 72.22 | 84.44 | 0.8906 |
| E11 | 75.93 | 75.56 | 74.44 | 76.67 | 0.8839 |
| E12T | 82.59 | 81.11 | 76.67 | 85.56 | 0.8939 |
| E12B | 78.89 | 76.94 | 71.11 | 82.78 | 0.8996 |


<!-- PDF page 19 -->

## Transformer Heads and the Quantum Accuracy Gap

The Transformer controls answer the most direct question in the report: what changes when the six dimensional representation is held fixed and only the decision head changes? MLP accuracy is 83.70% compared with 81.11% for VQC, a gap of 2.59 percentage points. Balanced accuracy differs by 2.78 points in favour of the MLP [P1].

The RBF SVM provides a useful contrast. It reaches 81.85% accuracy and 78.06% balanced accuracy. VQC has slightly lower accuracy but slightly higher balanced accuracy, 78.61%. Its sensitivity is 71.11% rather than 66.67%, while specificity is 86.11% rather than 89.44%. This is a tradeoff, not universal quantum superiority.

The ranking does not support claiming that a nonlinear quantum circuit is automatically preferable to a simple classifier. The seven parameter linear head obtains 83.33% accuracy and 81.39% balanced accuracy. Much of the class separation may already be available in the learned embedding, leaving little room for a more elaborate head.

The primary defence should acknowledge the best matched baseline and then explain the research value of the controlled comparison. The circuit is competitive with one control on balanced accuracy and weaker than others. Its practical utility must also account for resource cost, stability and independent validation. No result here establishes a deployment advantage.


Figure values: Linear: 81.39, MLP: 81.39, RBF SVM: 78.06, VQC: 78.61, No CNOT: 81.11


<!-- PDF page 20 -->

## Bi LSTM Heads and Class Specific Errors

The Bi LSTM results show a larger gap between VQC and the simplest matched control. The linear head reaches 81.11% accuracy and 79.44% balanced accuracy, whereas VQC reaches 75.93% and 75.56%. The balanced accuracy difference is minus 3.89 percentage points for VQC relative to linear [P1].

The source of this gap is not a sensitivity collapse. Both models have sensitivity 74.44%. Specificity falls from 84.44% for linear to 76.67% for VQC. Thus more healthy recordings receive positive labels under the saved VQC operating points. This distinction matters during a viva: saying that the quantum model misses more epilepsy cases would misdescribe this particular comparison.

The Bi LSTM RBF SVM obtains 80.37% accuracy, 78.33% balanced accuracy and 72.22% sensitivity. VQC sensitivity is slightly higher but its total and balanced accuracy remain lower. The no CNOT circuit improves balanced accuracy to 76.94%, still below the linear control.

These findings indicate that quantum head behaviour depends on the encoder rather than being an intrinsic fixed property of the classifier. They also caution against using only the Transformer result to describe the whole study. A transparent report presents both families and identifies which component changes between them.

The saved paired interval for VQC minus linear includes zero but extends further into negative values. This is uncertainty around a negative point estimate, not evidence that the two methods are equivalent. The small dataset cannot settle the expected gap on new participants.


| Bi LSTM head | Sensitivity % | Specificity % | Balanced % |
| --- | --- | --- | --- |
| Linear | 74.44 | 84.44 | 79.44 |
| MLP | 71.11 | 83.89 | 77.50 |
| RBF SVM | 72.22 | 84.44 | 78.33 |
| VQC | 74.44 | 76.67 | 75.56 |
| VQC without CNOT | 71.11 | 82.78 | 76.94 |


<!-- PDF page 21 -->

## Does Entanglement Help in the Saved Experiment

The no CNOT ablation improves the Transformer balanced accuracy point estimate from 78.61% to 81.11%, a gain of 2.50 percentage points. Accuracy increases from 81.11% to 82.59%. For Bi LSTM, balanced accuracy increases from 75.56% to 76.94% and accuracy from 75.93% to 78.89% [P1].

The saved paired comparison for Transformer entangled VQC minus no CNOT spans zero. The Bi LSTM comparison does as well. Therefore the result supports a descriptive statement about point estimates, not a general law that entanglement harms EEG classification. It does clearly undermine a claim that the entangling ring is the demonstrated source of the method's success.

This outcome is aligned with the kind of design question raised in the benchmarking study [2]. The relevant issue is whether a quantum resource contributes to the learning objective under a controlled ablation. Simply adding CNOT gates does not establish that the decision function gains a useful bias for the data.

The no CNOT model still contains rotation encoding and trainable local rotations. Its result is not an advantage demonstration: such a small nonentangling circuit admits a simple classical description. It is a diagnostic control that helps explain what the full architecture does not yet justify.

The most defensible conclusion is that entanglement is unnecessary for the best point estimate within these saved circuit variants. A later study could compare topology, depth and encoding while keeping search budgets fixed, but no such experiments were conducted for this report. Negative ablations belong in the main discussion because they prevent attributing every improvement to the most novel component.


Figure values: T VQC: 78.61, T no CNOT: 81.11, B VQC: 75.56, B no CNOT: 76.94


<!-- PDF page 22 -->

## End to End Fine Tuning

Fine tuning changes the embedding and head jointly, so it is analysed separately from frozen comparisons. Transformer VQC accuracy rises from 81.11% in the frozen case to 82.96% after fine tuning. Balanced accuracy increases from 78.61% to 79.72%. ROC AUC reaches approximately 0.9030 [P1].

The fine tuned Transformer MLP still has a higher balanced accuracy point estimate of 81.67% and accuracy of 84.44%. Transformer linear gives 80.83% balanced accuracy. The VQC improvement therefore does not close the complete gap to the strongest classical head under the recorded protocol.

For Bi LSTM, fine tuned VQC balanced accuracy is 78.06%, equal to the fine tuned linear point estimate and below the fine tuned MLP at 79.17%. Frozen Bi LSTM VQC had 75.56% balanced accuracy. Adaptation helps that quantum branch in this experiment, but it also changes the conditions of comparison.

These differences cannot be assigned exclusively to quantum learning. A trainable encoder can move its representation toward the selected head's preferred function family. Its additional optimisation opportunities are shared by the classical fine tuned controls, which must be retained when evaluating benefit.

The paired intervals for fine tuned comparisons do not establish a VQC advantage. The appropriate interpretation is modest: end to end adaptation reduces some of the observed performance loss and confirms that gradients can support joint optimisation. It does not demonstrate better data efficiency, lower compute cost or superior generalisation on new participants. The saved gradient checks support differentiability, while the predictive scores address a separate question.


| Fine tuned model | Accuracy % | Balanced % | AUC |
| --- | --- | --- | --- |
| FT-T-lin | 83.70 | 80.83 | 0.9033 |
| FT-T-mlp | 84.44 | 81.67 | 0.8952 |
| FT-T-vqc | 82.96 | 79.72 | 0.9030 |
| FT-B-lin | 80.00 | 78.06 | 0.8974 |
| FT-B-mlp | 79.63 | 79.17 | 0.8978 |
| FT-B-vqc | 79.63 | 78.06 | 0.8978 |


<!-- PDF page 23 -->

## Sensitivity Across Archived Configurations

The earlier full run gives Transformer VQC 77.41% accuracy and 76.11% balanced accuracy. The enhanced complete run gives 81.11% and 78.61%. Bi LSTM VQC balanced accuracy changes from 74.72% to 75.56% [P1, P4]. These shifts indicate sensitivity to architecture and training configuration on the same underlying dataset.

The enhanced implementation includes a deeper circuit, input calibration and broader optimisation choices. Several changes occur together, so the improvement cannot be attributed to circuit depth alone. The earlier and enhanced runs are not a controlled single factor ablation. They also do not supply independent external test cohorts.

The later waveform augmentation archive has its own unaugmented baseline. Its Transformer VQC balanced accuracy is 78.06%, not 78.61%, and its Bi LSTM VQC balanced accuracy is 77.50%, not 75.56% [P2]. An augmentation effect must therefore be calculated against that archive's own baseline. Subtracting the earlier complete run from an augmented model would combine treatment effects with run differences.

These details are important for avoiding accidental best result selection. The report specifies which experiment supports each sentence and does not average all folders into a single headline. A folder with a later timestamp is not automatically more authoritative when its final report is missing.

The observed variability also limits mechanistic explanations. A lower quantum result can reflect representation, optimiser, threshold and finite sample interactions. The saved artifacts identify performance changes but do not isolate their causal contribution. A rigorous defence describes these as plausible factors and points to the controls that would be needed to distinguish them.


| Run | Transformer VQC balanced % | Bi LSTM VQC balanced % |
| --- | --- | --- |
| Earlier full | 76.11 | 74.72 |
| Enhanced complete | 78.61 | 75.56 |
| Later baseline | 78.06 | 77.50 |
| Later waveform augmented | 79.44 | 82.50 |


<!-- PDF page 24 -->

## Activities Shared by Both Classes

The paired activity analysis excludes activities represented only in healthy recordings. It retains 77 files across desk work, idle sitting, jogging, laying, running, sitting, stairs and walking. This is a useful sensitivity analysis for class correlated activity coverage, but it is not a replacement for participant independent testing [P1].

Transformer VQC balanced accuracy falls from 78.61% on all recordings to approximately 77.40% in the paired activity subset. The Transformer MLP remains higher at about 80.11%. Bi LSTM VQC falls to approximately 73.04%, while its linear control is about 77.65%. The broader ranking therefore does not disappear when healthy only activities are removed.

The restricted analysis helps distinguish two questions. The all activity estimate describes the archive as supplied. The paired subset reduces one obvious activity and class imbalance, but keeps the same unknown participant structure and duplicate idle sitting signals. It does not establish that every retained activity is equally represented or free from nuisance differences.

The subset metrics come from restricting existing out of fold predictions. They do not retrain models using only the 77 files. Models may have learned from healthy only activities in their training partitions. The analysis therefore tests performance on a restricted test population under the original training procedure, not a fully redesigned balanced activity study.

Per activity estimates also contain few observations. A perfect score on a healthy only activity is a specificity observation, not evidence that epilepsy cases from that activity would be detected. This distinction should remain visible whenever activity charts are used in the presentation.


| Population | Interpretation |
| --- | --- |
| All 90 files | Original archive distribution |
| 77 shared activity files | Restricted test subset of saved predictions |
| Healthy only activity | Cannot estimate within activity sensitivity |
| All subsets | Unknown participant independence remains |


<!-- PDF page 25 -->

## Transfer to an Unseen Activity

Leave one activity out evaluation trains on other eligible activities and tests on a held out activity. Validation is selected from the training activities. This is a more demanding shift than ordinary recording grouped cross validation, because the model must generalise beyond the activity conditions used for fitting [P1].

The archived enhanced results vary sharply. Transformer VQC balanced accuracy is 90.00% for held out walking but approximately 38.89% for held out sitting and 45.56% for running. Bi LSTM VQC reaches 83.33% for jogging and about 33.33% for laying. These are descriptive means across seeds with tiny activity specific samples.

This heterogeneity is stronger evidence of a deployment boundary than a single pooled accuracy. The model is not uniformly activity robust. A high walking result cannot compensate for poor generalisation under another condition if an intended application must operate reliably across both.

No quantum superiority follows from isolated activity wins. Classical controls also fluctuate. The held out task changes class composition, sample size and nuisance structure; one activity may contain only a few epilepsy recordings. Accuracy increments can therefore be large when one prediction changes.

The report recommends presenting the full range and the per activity counts beside any selected examples. These tests assess transfer across labelled activity categories in the same archive, not transfer across sensors, hospitals or new participants. Missing participant identifiers and duplicate content remain unresolved even in an activity held out design.


Figure values: Desk work: 67.46, Idle sitting: 66.67, Jogging: 75.00, Laying: 50.00, Running: 45.56, Sitting: 38.89, Stairs: 72.22, Walking: 90.00


<!-- PDF page 26 -->

## Synthetic Corruption Robustness

The saved noise study perturbs test recordings with Gaussian noise, low frequency drift, EMG like corruption and ocular like corruption at several signal to noise ratios. The models and preprocessing statistics remain fixed. This tests sensitivity to a controlled signal change rather than benefiting from refitting on a corrupted test set [P1].

Synthetic EMG like and ocular like signals are proxies. They are not measured muscle or eye artefacts from an independent acquisition. The experiment therefore cannot establish tolerance to natural movement contamination or prove clinical robustness. Its value is a reproducible stress test with an explicit corruption generator and amplitude reference.

An important technical point is that SNR is referenced to the raw signal in the saved configuration. Subsequent WOSG filtering can attenuate some injected components. The nominal input SNR is not necessarily the SNR of the transformed features. A small measured degradation may reflect filtering and the corruption spectrum, not intrinsic robustness of the quantum head.

The chart reports average changes at the lowest tested SNR across the four corruption types for selected frozen heads. Averaging is a compact summary, not a claim that all corruptions have the same effect. Positive changes can occur through threshold effects or sampling variability and should not be interpreted as evidence that noise improves a medical system.

To defend a robustness claim, compare matched classical and quantum heads under the same corruption, use the clean operating threshold and report both sensitivity and specificity. The stored study is exploratory and shares the independence limitations of the clean evaluation. It supplies evidence about these defined perturbations, not a general reason to deploy the quantum branch.

At 5 dB, averaging the four corruption types at recording level gives Transformer VQC balanced accuracy of 66.88%, down 11.74 points from clean. Transformer MLP falls to 68.33%, down 13.06 points. Bi LSTM VQC reaches 66.18%, down 9.38 points. A smaller drop from a weaker clean starting point is not evidence of better absolute robustness. All three remain substantially below their clean performance.


<!-- PDF page 27 -->

## Why the Quick MixUp Comparison Is Inconclusive

The quick comparison is labelled without augmentation at alpha zero and with MixUp at alpha 0.15. It uses one seed and five recording grouped folds. Its saved recording_metrics.csv, summary_metrics.csv, fold_metrics.csv, paired_model_comparisons.csv and activity metrics are byte identical between conditions [P3, P5].

Inspection of hybrid_quantum_eeg_epilepsy.py finds no MixUp application in its training routine. The augmentation driver records that base script as the pipeline used. The MixUp setting therefore has no demonstrated active effect in this code path. Different timings or a changed configuration label do not establish that synthetic mixtures reached the optimiser.

The observed equality must not be presented as proof that augmentation is useless or that the model is insensitive to MixUp. It is evidence that this particular intervention comparison does not demonstrate an effective treatment. The stronger wording, supported by the visible code, is that the intended setting appears inactive in the archived pipeline.

This issue differs from the later waveform augmentation study, which has generated sample counts and changed model outputs. The two experiments should be named separately throughout the report and presentation. Calling both simply augmentation would allow an invalid result to obscure a potentially informative one.

No correction or rerun was attempted. The existing quick scores can still describe the quick baseline, but the difference between conditions should be withheld as evidence about MixUp efficacy. This is a substantive methodological finding from the result review and a useful example of why configuration files must be checked against executable behaviour.


| Artifact or check | Observed result |
| --- | --- |
| Recording metric file hashes | Identical |
| Fold metric file hashes | Identical |
| Activity metric file hashes | Identical |
| Base script MixUp application | Not present |
| Inference about MixUp benefit | Not supported by this comparison |


<!-- PDF page 28 -->

## Waveform Augmentation in the Later Archive

The later archive contains baseline and AUG prefixed models generated with a distinct waveform augmentation procedure. Its configuration specifies moderate perturbations of epilepsy training windows, including amplitude changes, small Gaussian noise, slow drift and sample shifts. The generation audit records two additional synthetic windows per source positive training window; one example fold reports 72 source epilepsy windows and 144 generated windows [P2].

The most favourable quantum change is Bi LSTM VQC: balanced accuracy rises from 77.50% to 82.50%, sensitivity from 73.33% to 84.44%, and accuracy from 78.89% to 81.85%. Specificity changes from 81.67% to 80.56%. The gain is mainly a shift toward detecting more positive recordings, with a small specificity cost.

Transformer VQC shows a smaller balanced accuracy rise from 78.06% to 79.44%. Its sensitivity increases from 75.56% to 80.00%, while specificity falls from 80.56% to 78.89%. This demonstrates why augmentation should be interpreted through class specific errors rather than treated as an automatic accuracy improvement.

The augmented Bi LSTM linear head gives 81.11% balanced accuracy, so augmented VQC has a 1.39 point higher estimate against that control within this archive. This is a promising descriptive comparison. The aggregate augmentation summary does not provide a dedicated paired confidence interval for each treatment effect, and the archive lacks its final narrative report. The result therefore does not establish superiority or erase the duplicate leakage issue.

Because only the positive class is augmented, the treatment also changes the effective class exposure. Improved sensitivity could result from this reweighting as well as from useful waveform invariance. A later causal ablation would separate those effects; no new training was performed here.


| Model and condition | Accuracy % | Balanced % | Sensitivity % |
| --- | --- | --- | --- |
| E7 | 78.89 | 78.06 | 75.56 |
| AUG_E7 | 79.26 | 79.44 | 80.00 |
| E11 | 78.89 | 77.50 | 73.33 |
| AUG_E11 | 81.85 | 82.50 | 84.44 |
| AUG_E8 | 81.48 | 81.11 | 80.00 |


<!-- PDF page 29 -->

## Resource Cost and Parameter Efficiency

A small quantum head is not automatically more parameter efficient than a matched classical head. The enhanced VQC has 55 parameters, the MLP has 49 and the linear head has seven. Adding the same 25,734 parameter Transformer encoder gives total sizes of 25,789, 25,783 and 25,741 respectively. The quantum branch is not smaller than these controls [P1, P5].

The source of the 55 parameters is 36 circuit rotations, 12 input calibration values and seven readout values. Reporting only the rotations would omit trainable classical components. Comparing those 36 values against the entire neural encoder would mix head and pipeline accounting.

The archived selected fit timing also favours classical heads. Mean selected head fit time is approximately 19.86 seconds for Transformer VQC versus 0.41 seconds for MLP and 0.32 seconds for linear. Bi LSTM VQC is about 18.91 seconds versus 0.38 seconds for its MLP. These are descriptive timings from stored training rows, not end to end latency benchmarks.

The environment uses GPU acceleration for classical neural computation while the VQC statevector simulation executes on CPU. Timings include implementation and device effects and do not predict performance on future quantum hardware. They nevertheless provide no measured speedup in this project. They also exclude a complete accounting of search, feature extraction, data transfer and deployment inference.

Published resource savings in a different quantum architecture [3] cannot supply a missing result here. A valid defence can say that the head is compact in absolute terms and compatible with a six qubit simulation. It should also admit that the simpler classical controls are cheaper and at least as persuasive for practical use under the current evidence.


| Transformer head | Head parameters | Mean selected fit seconds |
| --- | --- | --- |
| Linear | 7 | 0.32 |
| MLP | 49 | 0.41 |
| VQC | 55 | 19.86 |


<!-- PDF page 30 -->

## Plausible Reasons for Lower Quantum Accuracy

The saved evidence supports several hypotheses, but not a single proven mechanism. The first is representational mismatch. The encoder is pretrained with a classical MLP objective, then frozen. A six dimensional representation useful to that objective need not align with the function family available to a particular quantum encoding and readout. Fine tuning improves some VQC scores, consistent with adaptation helping, although it does not isolate the cause [P1].

The second is limited encoding structure. The implemented circuit encodes the input once, applies a fixed small variational topology and measures local Z expectations. Additional trainable gates do not necessarily supply the input dependence needed to fit the class boundary. This is a reason to inspect the actual encoding rather than infer expressive power from the number of amplitudes.

Third, the sample size and model selection process can dominate small differences. Only 30 positive recordings are available, repeated across seeds. Validation selected thresholds and early stopping can change sensitivity and specificity. The negative point estimates should be reported, but their exact magnitude may not reproduce on a new population.

Fourth, the circular CNOT structure may impose an unhelpful bias. The no CNOT point estimates are better in both enhanced branches. This observation suggests a topology question; it does not establish a universal disadvantage of entanglement.

Two common excuses are not justified. Hardware noise cannot explain these scores because the circuit uses an ideal statevector simulator. A barren plateau diagnosis also requires gradient behaviour beyond the saved nonzero gradient checks. Lower accuracy by itself does not demonstrate vanishing gradients. Likewise, more qubits, deeper circuits or longer training cannot be promised to solve the gap without controlled evidence.


<!-- PDF page 31 -->

## How to Use the VQC Papers in the Defence

The literature should be used to justify the question and delimit the interpretation, not to excuse every unfavourable outcome. Each reference below supplies one specific argument. The local evidence must then show whether that argument applies to this architecture and dataset.

The central distinction is between an explanation and a demonstrated benefit. Encoding limitations can explain why a circuit may be a poor match. They cannot establish that an untested encoding would outperform MLP. A generalisation theorem can motivate research on compact models, but cannot validate duplicated clinical recordings. A favourable benchmark in another domain does not transfer its score to wearable EEG.

For the viva, name the relevant control immediately after discussing a paper. For resource claims, show the 55 versus 49 versus seven parameter table. For entanglement, show E7 versus E12T. For small sample uncertainty, show the paired interval and admit that participant independence is unavailable. This makes the defence testable against the actual results.

The preferred position is that the project examines a credible modelling hypothesis and reports a mixed outcome. It avoids a stronger claim than its data support, while preserving a clear technical contribution in representation, matched comparison and result auditing.


| Reference | Permitted argument | Required qualification |
| --- | --- | --- |
| Bowles et al [2] | Classical wins and ablations are informative | Not validation of this dataset |
| Circuit centric model [3] | Measure compactness and resources | Our VQC is not smaller than MLP |
| Huang et al [4] | Advantage is task dependent | No separation shown here |
| Caro et al [5] | Complexity affects generalisation | No automatic small data guarantee |
| Encoding study [6] | Input encoding constrains the model | No new encoding was tested |
| Re uploading [7] | Repeated encoding is a design option | Current model encodes once |
| McClean et al [8] | Trainability can be difficult | Barren plateaus not diagnosed |


<!-- PDF page 32 -->

## A Defensible Discussion for the Report

The following discussion is suitable for adaptation into the submitted report because it states both the result and the limitation.

The quantum component was investigated as an alternative decision function on a controlled low dimensional EEG representation. In the complete enhanced experiment, Transformer VQC achieved 81.11% accuracy and 78.61% balanced accuracy, whereas the matched MLP achieved 83.70% and 81.39%. Thus, the present results do not show a predictive advantage over the strongest classical control. The small positive balanced accuracy difference against RBF SVM is specific to that comparator and accompanies lower overall accuracy.

This outcome does not invalidate the architectural experiment. It establishes that replacing a classical head with this particular simulated circuit is feasible, but not sufficient to improve the best available result. The no CNOT comparison further shows that the entangling ring is not required for the strongest circuit point estimate in this run. The practical finding is therefore a boundary on the usefulness of this VQC design under the selected representation and evaluation budget.

The paired uncertainty intervals leave the true difference unresolved within a broad range; they do not establish equivalence. Likewise, improved Bi LSTM VQC sensitivity in the separate waveform augmentation archive is encouraging but remains conditional on that experiment's treatment and shared dataset. It cannot be presented as a general quantum advantage.

The evidence has limitations that affect both classical and quantum models. Identical signal contents cross partitions, activity coverage is class dependent and participant identifiers are unavailable. Accordingly, the scores describe the archived protocol and should not be represented as independent patient performance. A future study should correct content grouping and obtain subject identifiers before increasing model complexity. The present contribution is an honest, reproducible comparison and a documented basis for that next study [P1-P5].


<!-- PDF page 33 -->

## Viva Questions and Suggested Answers

Why use a quantum model if accuracy is lower? The objective was to test whether a parameterised quantum head adds value to the same learned EEG representation. The answer is mixed and mostly negative against the strongest controls. Showing that boundary with matched comparisons is a valid research outcome, although it does not justify choosing the quantum model for deployment.

Can you say the methods are equivalent because the difference is not significant? No. The paired interval includes zero and also allows meaningful losses. We did not define and test an equivalence margin. We can say that superiority is not established and that the dataset gives imprecise estimates.

Is hardware noise responsible for the lower result? No. The saved quantum branch uses ideal statevector simulation with default.qubit. We cannot attribute a simulator result to physical gate errors that were not modelled.

Does the quantum model use fewer parameters? Not against our matched controls. Its head has 55 trainable parameters, versus 49 for MLP and seven for linear. Most parameters belong to the common classical encoder. Compactness is an architectural description here, not a measured resource advantage.

What does removing CNOT gates tell you? The point estimates improve without the ring in both enhanced encoders. We therefore do not claim that entanglement caused the predictive performance. The paired uncertainty still prevents a universal conclusion about entanglement.

What is the strongest weakness in the evaluation? Recording identifiers keep each file's windows together, but three identical healthy signal contents cross partitions. Subject identifiers are also absent. We disclose these issues and do not claim independent patient generalisation.

Maam, quantum side ki accuracy kam hai to defence kya hai? Humne quantum advantage claim nahi kiya. Same embeddings aur same splits par fair comparison kiya hai. VQC trainable hai aur useful discrimination deta hai, lekin best classical head abhi better hai. Hamara contribution controlled comparison, ablation aur limitations ko clearly establish karna hai.


<!-- PDF page 34 -->

## Threats to Validity and Clinical Interpretation

Internal validity is limited by identical signal content crossing train, validation and test roles. This is a concrete finding, not a hypothetical warning. Missing historical source snapshots also limit exact attribution of saved outputs to every current code line. Stale generated labels about circuit depth and dropout require preference for configuration and tensor evidence [P1, P5].

Construct validity concerns the target label. The archive identifies healthy and epilepsy labelled recordings, not verified onset and offset annotations for every window. Recording classification accuracy does not measure seizure event sensitivity, prediction horizon or false alarm burden over continuous use. Terms such as seizure detector should therefore be qualified in the report title, abstract and conclusions.

External validity is limited by a small, single channel dataset with activity imbalance, unknown participant identity and possible saturation. The result cannot establish performance across patient ages, sensor placements, acquisition sessions or hospitals. High classification scores on a related multichannel dataset do not remove these constraints.

Statistical validity is limited by repeated use of the same 90 recordings across seeds, exploratory comparisons and confidence intervals based on a questionable independence unit. The saved bootstrap intervals describe the archived analysis; they should not be read as precise population guarantees. Small activity subsets make per activity rankings particularly unstable.

Practical validity requires latency, energy, calibration, false alarms and robust operation outside the laboratory. These quantities are not established by the saved tables. The VQC runs in simulation and has no demonstrated hardware speedup. The report therefore presents a research prototype and benchmark analysis rather than a medical product or clinical decision aid.

Acknowledging these limits does not diminish the technical work. It makes the conclusion proportionate to the evidence and identifies which additional information would materially strengthen a future study.


<!-- PDF page 35 -->

## Recommendations for the Next Research Stage

The first priority is data independence, not a more elaborate circuit. Group identical signal hashes before any future split or remove duplicates under a documented rule. Seek participant and session identifiers from the dataset maintainers. Preserve an external evaluation set if one becomes available, and define the intended task as recording classification or event detection before selecting metrics.

The second priority is intervention validity. The quick MixUp comparison should be marked inconclusive in presentations. A future implementation should log actual mixed batches or generation counts and demonstrate that the intended intervention is active. Waveform augmentation should be compared against a class exposure matched control so its effect is not confused with oversampling.

For quantum design, compare a limited number of prespecified encodings, circuit depths and entangling topologies under equal search budgets. Include linear and MLP heads on exactly the same representation. Report the no CNOT control even when it performs better. Any circuit improvement should be assessed on a validation plan fixed before the final evaluation.

For statistical analysis, select a primary metric such as recording balanced accuracy and specify meaningful effect sizes before testing. Use paired comparisons and a resampling unit that reflects the actual independent participant or content group. If equivalence is the objective, choose a justified margin prospectively and plan the sample size accordingly.

For practical claims, measure complete preprocessing and inference cost, not only selected training fit seconds. Hardware execution would require shot budgets, noise assumptions, repeated evaluations and matched classical resource reporting. These are future recommendations only. No experiments in this list were executed while preparing the report.

The existing project already contains enough evidence for an honest academic discussion. The report should be submitted as a draft analysis of the saved protocol, with the duplicate finding and unsupported quantum advantage claims addressed explicitly.


<!-- PDF page 36 -->

## Conclusion

This project combines a wearable EEG time frequency pipeline with classical temporal representation learning and simulated six qubit classification. Its strongest methodological feature is the attempt to compare heads on identical low dimensional embeddings while retaining classical baselines and an entanglement ablation. Its saved results support useful discrimination but do not show a general quantum advantage.

In the complete enhanced experiment, Transformer VQC obtains 81.11% accuracy and 78.61% balanced accuracy. The matched MLP obtains 83.70% and 81.39%. VQC slightly exceeds RBF SVM in balanced accuracy while losing in total accuracy, demonstrating a comparator specific sensitivity and specificity tradeoff. Bi LSTM VQC performs below its linear control on balanced accuracy. Fine tuning helps some quantum branches, but the strongest classical alternatives remain competitive or better.

The no CNOT point estimates are higher than the corresponding entangled circuit estimates. A later waveform augmentation archive shows a five point Bi LSTM VQC balanced accuracy gain against its own baseline, with improved sensitivity and slightly reduced specificity. The quick MixUp pair, however, has identical metric outputs and no demonstrated active MixUp path. These experiments cannot be combined into one augmentation claim.

The most consequential audit result is that three identical healthy signal contents cross partitions. Together with unavailable participant identifiers and asymmetric activity coverage, this limits the interpretation of every saved score. The report therefore does not describe the results as independent patient performance, clinical validation, quantum speedup or evidence of reduced model size.

The scientific defence is a clear statement of what was learned: a VQC can be integrated and optimised in this pipeline, but this circuit does not improve the strongest matched classical baseline under the recorded conditions. That conclusion is informative when accompanied by ablations, uncertainty, resource accounting and candid limitations. Further claims should follow stronger data and controlled evidence rather than enthusiasm for the quantum component.


<!-- PDF page 37 -->

## References for Quantum Interpretation

[1] S. Dash, D. K. Dash, R. K. Tripathy and R. B. Pachori. Time-frequency domain machine learning for detection of epilepsy using wearable EEG sensor signals recorded during physical activities. Biomedical Signal Processing and Control 100, 107041, 2025.
https://doi.org/10.1016/j.bspc.2024.107041

[2] J. Bowles, S. Ahmed and M. Schuld. Better than classical? The subtle art of benchmarking quantum machine learning models. arXiv:2403.07059, 2024 preprint.
https://arxiv.org/abs/2403.07059

[3] M. Schuld, A. Bocharov, K. M. Svore and N. Wiebe. Circuit-centric quantum classifiers. Physical Review A 101, 032308, 2020.
https://doi.org/10.1103/PhysRevA.101.032308

[4] H.-Y. Huang et al. Power of data in quantum machine learning. Nature Communications 12, 2631, 2021.
https://doi.org/10.1038/s41467-021-22539-9

[5] M. C. Caro et al. Generalization in quantum machine learning from few training data. Nature Communications 13, 4919, 2022.
https://doi.org/10.1038/s41467-022-32550-3

[6] M. Schuld, R. Sweke and J. J. Meyer. Effect of data encoding on the expressive power of variational quantum-machine-learning models. Physical Review A 103, 032430, 2021.
https://doi.org/10.1103/PhysRevA.103.032430

Web references were checked on 17 November 2026 using primary paper records or publisher pages. Interpretations in this report distinguish theoretical results, simulations and measurements from the local project. No paper is cited as evidence that this particular dataset establishes quantum advantage.


<!-- PDF page 38 -->

## References for Encoding and EEG Context

[7] A. Perez-Salinas, A. Cervera-Lierta, E. Gil-Fuster and J. I. Latorre. Data re-uploading for a universal quantum classifier. Quantum 4, 226, 2020.
https://doi.org/10.22331/q-2020-02-06-226

[8] J. R. McClean, S. Boixo, V. N. Smelyanskiy, R. Babbush and H. Neven. Barren plateaus in quantum neural network training landscapes. Nature Communications 9, 4812, 2018.
https://doi.org/10.1038/s41467-018-07090-4

[9] R. Sharma and R. B. Pachori. Classification of epileptic seizures in EEG signals based on phase space representation of intrinsic mode functions. Expert Systems with Applications 42, 1106-1117, 2015.
Local supplied PDF: EEG_Seizure_Classification_Phase_Space_IMFs_2015.pdf

[10] R. Sharma, R. B. Pachori and U. R. Acharya. Application of entropy measures on intrinsic mode functions for the automated identification of focal electroencephalogram signals. Entropy 17, 669-691, 2015.
https://doi.org/10.3390/e17020669

[11] A. Bhattacharyya, R. B. Pachori, A. Upadhyay and U. R. Acharya. Tunable-Q wavelet transform based multiscale entropy measure for automated classification of epileptic EEG signals. Applied Sciences 7, 385, 2017.
Local supplied PDF: Epileptic_EEG_Classification_Tunable_Q_Wavelet_Multiscale_Entropy_2017.pdf

[12] A. Bhattacharyya and R. B. Pachori. A multivariate approach for patient-specific EEG seizure detection using empirical wavelet transform. IEEE Transactions on Biomedical Engineering 64, 2003-2015, 2017.
Local supplied PDF: Patient_Specific_EEG_Seizure_Detection_Multivariate_EWT_2017.pdf

The supplied second order difference, sleep corpus and air writing papers were inspected for scope but were not used to support the reported wearable epilepsy scores. The duplicate local copy of reference [1] was counted once. Local PDF sources are retained in the project folder for verification. No historical result from another dataset is presented as a new project measurement.


<!-- PDF page 39 -->

## Project Evidence Register

The following paths resolve the project citations used throughout the report. Paths are relative to the workspace root. Long directory names are separated below for readability; they identify the original saved artifacts and not newly generated experiments.

[P1] outputs/experiment_20261116_143634. Primary files: config/config.json, config/dataset_manifest.csv, config/fold_assignments.csv, config/model_parameter_counts.json, metrics/recording_metrics.csv, metrics/paired_model_comparisons.csv, metrics/recording_metrics_paired_activities_only.csv, metrics/activity_holdout_summary.csv, metrics/noise_robustness_metrics.csv and metrics/training_summary.csv. The reports subdirectory provides the saved methodology, audit and final narrative.

[P2] outputs/experiment_20261116_202913. Secondary waveform augmentation evidence: config/config.json, metrics/recording_metrics.csv, metrics/augmentation_generation_audit.csv and metrics/augmentation_ablation_summary.csv. Baseline and AUG models are compared only within this archive. The final_experiment_report.md file is absent.

[P3] outputs_gwst_vqc_ablation. Comparison runs are without_augmentation/experiment_20261117_100749 and with_mixup_augmentation/experiment_20261117_101255. Their metrics and configuration files support the inactive intervention finding. The directory level augmentation report records the base script used.

[P4] outputs/experiment_20261116_095358. Earlier full profile results used only for sensitivity across archived configurations. Smoke and quick development runs were inventoried but do not supply headline performance estimates.

[P5] report_work/audit.json and report_work/audit.py. Read only calculations document manifest hash groups, their split roles, saved parameter counts, fit timing summaries and metric file equality. No models are fitted in this audit.

[P6] hybrid_quantum_eeg_epilepsy.py, hybrid_quantum_eeg_epilepsy_enhanced.py, hybrid_quantum_eeg_epilepsy_augmented.py and run_gwst_quantum_augmentation_ablation.py. The source inspection establishes current visible training paths and circuit structure, with saved configurations preferred over stale prose descriptions. Repository source: https://github.com/Dev-Goyal0808/miniproject at revision 75b5971.


<!-- PDF page 40 -->

## Submission Notes and Claim Boundaries

This report is a 40 page academic draft based on the available results. Before submission, add the institution's required cover information, student names, registration numbers and supervisor details using verified information. A signed declaration, approval certificate or institutional endorsement should only be added through the actual approval process.

The conclusion can be defended without claiming quantum superiority. State the research question, identify the best matched classical baseline, show the quantum gap and explain what the ablations establish. Keep the duplicate content limitation visible. If asked whether retraining has corrected it, the answer is no: this report preserves the existing results and does not manufacture a corrected score.

For an accompanying presentation, use one primary results table, one head comparison chart, the no CNOT ablation and the within archive waveform augmentation comparison. Include the 55 versus 49 versus seven parameter accounting. Avoid combining the best quantum score from one folder with a weaker classical score from another.

Use cautious, specific language. Supported statements include simulated VQC integration, useful recording discrimination under the archived protocol, a negative point estimate against the strongest frozen control and a descriptive augmentation improvement in one branch. Unsupported statements include quantum advantage, fewer parameters than the matched MLP, hardware noise as the measured cause of lower accuracy, clinically validated seizure detection and patient independent performance.

The editable companion Markdown contains the same page sections and numerical tables, so college formatting can be applied without copying text from a PDF. Reformatting may change pagination; the supplied PDF is the fixed 40 page version. The audit and builder scripts remain in report_work for traceability.

No training, fine tuning, model inference on new data or test threshold search was performed during preparation. All figures and tables represent saved measurements or explicitly identified arithmetic summaries. The final position is proportionate to those measurements: a transparent controlled study with valuable negative findings, meaningful methodological limitations and a clear path for stronger future evidence.