"""Research paper revision using saved results only. No model code is imported."""
from pathlib import Path
import copy,json,csv

def revise(old,root,M,L,base_refs):
    p=[]
    def add(title,text,table=None,figures=None,chart=None):
        p.append(dict(title=title,text=text.strip(),table=table,chart=chart,figures=figures or []))
    def use(index,title=None,figures=None,table=True,chart=False):
        item=copy.deepcopy(old[index-1]);item['title']=title or item['title'];item['figures']=figures or []
        if not table:item['table']=None
        if not chart:item['chart']=None
        p.append(item)
    def figure(name,height,caption):return (str(root/'outputs/experiment_20261116_143634/plots'/name),height,caption)
    def generated(name,height,caption):return (str(root/'report_work/revision_figures'/name),height,caption)

    add('Abstract', '''Hybrid Quantum Classical Classification of Wearable EEG Recordings

Wearable electroencephalogram classification is challenged by motion contamination, nonstationary activity and small labelled datasets. This study analyses a hybrid pipeline combining wavelet domain filtering, the Gaussian window Stockwell transform, temporal encoders and a six qubit variational quantum classifier. The research question is whether the quantum decision head adds predictive value beyond classical heads receiving the same learned representation.

The saved dataset audit contains 90 recordings, with 60 healthy and 30 epilepsy labelled files. Four non overlapping five second windows are obtained from each recording. Random forest, support vector machine and mutual information baselines use 450 handcrafted features. Transformer and bidirectional LSTM encoders instead map temporal GWST tokens to six dimensional embeddings, followed by linear, MLP, RBF SVM or VQC heads. The main complete enhanced experiment uses three seeds and five recording grouped folds. This report analyses existing artifacts; no additional training was performed.

Transformer VQC achieves 81.11% recording accuracy, 78.61% balanced accuracy and 0.8919 ROC AUC. Transformer MLP achieves 83.70%, 81.39% and 0.9022. The paired balanced accuracy difference is minus 2.78 percentage points, with a saved 95% interval from minus 6.82 to plus 1.80 points. Removing CNOT gates improves the Transformer circuit point estimate. A separate waveform augmentation archive improves Bi LSTM VQC balanced accuracy from 77.50% to 82.50% against its own baseline.

The reference paper reports 90.74% RF accuracy under a different frame based protocol; direct ranking against the present recording grouped result is not justified. Duplicate signal contents crossing partitions, unavailable participant identifiers and class dependent activity coverage further restrict interpretation. The contribution is a controlled comparison and critical analysis of a simulated quantum head, rather than demonstrated quantum advantage or clinical validation.

Keywords: wearable EEG; epilepsy classification; Stockwell transform; Transformer; bidirectional LSTM; variational quantum classifier; matched baselines.''')

    add('1 Introduction', '''Electroencephalography provides a noninvasive record of electrical activity associated with neural processes. Wearable acquisition can extend recording beyond a conventional clinical session, but fewer electrodes, movement and changes in physical activity complicate interpretation. The classification task considered here distinguishes healthy from epilepsy labelled recordings in a public activities of daily living archive [1,13]. It does not establish that every positive window contains an annotated seizure.

Time frequency analysis is suitable for signals whose spectral characteristics vary over time. Dash and colleagues [1] use Gaussian window Stockwell features with classical and deep learning models for wearable EEG. Their work supplies the base signal processing framework for this project. The present architecture retains a handcrafted branch while adding temporal token encoders and an explicit comparison between classical and variational quantum heads.

The motivation for the quantum component is experimental. A parameterised circuit defines a different family of nonlinear input to output functions, but there is no general reason to expect it to outperform well tuned classical models on a small classical dataset [2,4]. A useful investigation must therefore compare against strong controls and isolate what the circuit contributes. High dimensional quantum states alone do not demonstrate useful feature separation, lower complexity or practical speedup.

Two temporal encoders are considered. A Transformer uses attention to combine information across tokens, while a bidirectional LSTM processes the sequence in both directions. Both produce six dimensional embeddings. Matched heads consume the same representation, allowing the study to ask whether the classifier family improves prediction after encoding. Fine tuned variants are analysed separately because the encoder can adapt to its chosen head.

The report follows a research paper structure: literature survey, methodology, results and discussion, comparison with the base paper, and conclusion. The results section includes the saved repository plots and additional visual summaries calculated from the stored metrics. Numerical claims retain their experiment identity and do not pool unrelated runs.''')

    use(4,'1.1 Research Objectives and Contribution')
    p[-1]['text']+='\n\nThe contribution is evaluated through recording balanced accuracy, class specific errors, paired uncertainty, entanglement ablation and resource accounting. The practical goal is to establish what the implemented circuit achieves under a transparent protocol and where its benefit remains unproven.'

    add('2 Literature Survey of Wearable EEG', '''2.1 Dash et al 2025 as the base paper [1]

Dash and colleagues analyse epilepsy using wearable sensor EEG recorded during physical activities. Their processing chain includes wavelet domain motion artefact suppression, GWST analysis, L1 norm and Shannon entropy features, and machine learning or deep learning classifiers. The paper reports 90.74% RF accuracy in a hold out experiment and 74.44% average multilayer LSTM accuracy for a ten fold cross validation setting. These values belong to different protocols and must not be merged into one baseline score.

The direct relevance is the shared single channel wearable context, five second time frequency analysis and 450 feature construction. The current work extends that structure with temporal encoders and quantum heads. A limitation for exact reproduction is that the archived data and the paper describe different frame and duration totals. The present repository has 360 complete five second windows; the paper reports 540 frames in its wearable analysis. This discrepancy motivates the separate protocol comparison in Section 5.

2.2 Sharma and Pachori 2015 [9]

This study reconstructs phase space representations of intrinsic mode functions extracted from EEG. It uses measures such as confidence ellipse area and the distribution of distances in a reconstructed space, followed by least squares SVM classification of seizure and seizure free signals. The central idea is that nonlinear temporal structure can be represented by a small set of discriminative descriptors.

Its relevance is methodological: handcrafted summaries can encode information beyond a single power spectrum and should remain serious controls when evaluating a learned model. Its task and acquisition conditions differ from wearable healthy versus epilepsy recording classification. Consequently, its reported predictive performance is not transferred to the current dataset. The current project uses GWST magnitude features rather than EMD phase space features, and does not claim to reproduce this earlier study.''')

    add('2.3 Wavelet and Patient Specific EEG Studies', '''Bhattacharyya et al 2017 on tunable Q wavelets [11]

Bhattacharyya, Pachori, Upadhyay and Acharya develop a multiscale entropy approach based on the tunable Q wavelet transform. Decomposition into subbands allows entropy to characterise EEG complexity at different scales. The work studies classification of normal, seizure free and seizure signals and motivates the use of frequency resolved complexity measures in EEG analysis.

For this project, the relevant connection is the combination of a time frequency representation and entropy. The current feature vector computes entropy at GWST frequency rows, whereas the earlier method aggregates entropy over tunable Q wavelet subbands. They are related approaches, not the same transform or feature definition. The earlier study supports a signal processing rationale but cannot supply an expected accuracy for wearable activity recordings.

Bhattacharyya and Pachori 2017 on empirical wavelets [12]

This paper explores multivariate empirical wavelet decomposition for patient specific seizure detection. It derives joint amplitude and frequency information from automatically selected EEG channels and computes features within short moving windows. The supplied paper evaluates 177 hours of CHB MIT recordings and reports high cross validated detection performance in that multichannel setting.

The study illustrates the importance of matching analysis to the intended detection unit. It uses patient specific multichannel information and a seizure event context, while the present model uses one wearable channel and recording class labels. Missing participant identifiers in the wearable archive prevent the same patient specific or patient independent interpretation. Its strong results therefore cannot be used as a numerical target without reproducing the task, channels and validation structure.

Together, these two papers support comparing classical time frequency descriptors with learned representations. They also show why a literature survey should discuss datasets and validation alongside classifier names: a percentage from another task is not a fair ranking of architectures.''')

    add('2.4 Quantum Classifiers and Encoding', '''Schuld et al 2020 on circuit centric classifiers [3]

Schuld, Bocharov, Svore and Wiebe propose a low depth variational classifier using amplitude encoded inputs, trainable circuit gates and a measurement based output. Their study reports useful benchmark performance with compact parameterisation and discusses robustness and optimisation. Its relevance is the design of a trainable quantum decision function integrated with classical optimisation.

The wearable model differs in both encoding and resource balance. It uses six angle encoded embedding coordinates, input calibration and a classical readout. Its head has 55 parameters, compared with 49 for the matched MLP and seven for linear. Thus the earlier paper motivates measuring parameter count, but does not establish a parameter saving here. Resource claims must follow the actual architecture rather than the broader quantum model category.

Schuld Sweke and Meyer 2021 on encoding expressivity [6]

This work relates the input dependence of variational quantum models to a Fourier representation and shows that the encoding gates determine accessible frequencies. Repeating suitable encoding operations can enrich that function spectrum. It makes input encoding an explicit design choice rather than a neutral preprocessing step.

The implication for this project is that more variational rotations do not automatically yield the input dependence required by an EEG decision boundary. The implemented circuit encodes the calibrated embedding once. A different encoding or repeated upload is a future hypothesis, not a demonstrated remedy for the observed gap. Perez Salinas et al [7] supply a related repeated encoding construction, while McClean et al [8] establish trainability risks for classes of circuits. Neither result diagnoses the present model's optimisation solely from its accuracy.

These studies justify testing circuit architecture under controls. They do not justify attributing lower ideal simulator accuracy to physical hardware noise or promising that additional qubits must improve performance.''')

    add('2.5 Quantum Benchmarking and Generalisation', '''Bowles Ahmed and Schuld 2024 [2]

This benchmarking study systematically compares quantum learning models with classical alternatives and reports that conventional classifiers often perform better. It also investigates removing entanglement and finds cases with preserved or improved performance. The relevant contribution is a methodology for asking what a quantum component actually adds, rather than treating a positive score as sufficient evidence of advantage.

The present work follows that question through matched linear, MLP and RBF SVM heads and no CNOT controls. The observed classical wins and improved no CNOT point estimates are therefore legitimate design findings. The benchmarking paper does not validate the wearable labels, correct duplicate content leakage or demonstrate equivalence between the local models.

Caro et al 2022 [5]

Caro and colleagues analyse generalisation of variational quantum models trained from limited data. Their bounds connect generalisation behaviour to trainable gates and sample size, under stated assumptions. This provides a theoretical motivation for controlling circuit complexity and measuring how much capacity is actually trained.

The bound is not a certificate for the complete EEG pipeline. The classical encoder contains thousands of parameters, observations are repeated across seeds and identical signals cross partitions. A theorem about a model family cannot replace validation of the independent sampling unit. Huang et al [4] further motivate checking whether classical methods can exploit the available data before claiming a quantum learning separation.

Eight principal papers are surveyed in Sections 2.1 to 2.5: the wearable base paper, the phase space EEG study, the tunable Q entropy study, the multivariate empirical wavelet study, the circuit centric classifier, the encoding expressivity study, the quantum benchmark and the few data generalisation study. Supporting references supply the algorithms and software used in the methodology. The resulting research gap is a controlled assessment of a small simulated VQC on learned wearable EEG embeddings, with explicit disclosure of unfavourable results and data limitations.''')

    add('2.6 Literature Synthesis and Research Gap', """The eight principal studies address complementary parts of the research problem. Four EEG papers motivate time frequency analysis, nonlinear features and attention to validation context. Four quantum papers motivate controlled head comparisons, encoding analysis and restrained generalisation claims. Their contributions should be connected through the task they solve rather than arranged as an accuracy leaderboard.

The base paper is the closest application reference because it shares the wearable activity setting. The other EEG studies provide signal processing alternatives under different labels and channels. The quantum studies supply architecture and benchmarking principles rather than direct evidence on this wearable archive. No numerical result from those studies is substituted for a local measurement.

The resulting research gap is whether a compact simulated circuit contributes after a learned EEG representation when strong classical controls receive identical inputs. The present design tests that question using two encoders, several matched heads, a no CNOT ablation and separate fine tuning. Its contribution is the controlled comparison and its limitations, including negative findings, rather than a presumption of quantum superiority.

The broader bibliography contains 30 references. The additional sources document the dataset, filtering, foundational classifiers, sequence architectures, optimisation, regularisation and software. They support reproducibility and methodological explanation; they are not 30 independent validations of the proposed system.""",table=(['Principal study','Contribution','Connection to this study'],[['Dash et al [1]','Wearable GWST classification','Direct base pipeline'],['Sharma and Pachori [9]','IMF phase space features','Nonlinear classical control rationale'],['Bhattacharyya et al [11]','Wavelet multiscale entropy','Frequency resolved complexity'],['Bhattacharyya and Pachori [12]','Multivariate patient specific EEG','Task and validation distinctions'],['Schuld et al [3]','Circuit centric learning','Trainable quantum head'],['Schuld et al [6]','Encoding expressivity','Encoding design constraints'],['Bowles et al [2]','Quantum benchmarks','Strong baselines and ablations'],['Caro et al [5]','Generalisation analysis','Complexity and sample limitations']]))

    add('3 Methodology and Processing Architecture', '''The architecture has a common signal processing front end and two families of classification branches. A recording audit first identifies labels, activities, lengths and signal hashes. WOSG filtering is applied before complete five second segmentation. GWST magnitudes then support either handcrafted frequency summaries or temporal token learning.

The handcrafted branch forms 450 L1 and entropy values for RF, SVM and MI selected RF. The temporal branch creates 64 tokens, projects 225 frequency values to 32 coordinates and processes them with a Transformer or Bi LSTM. Attention pooling and a bounded bottleneck produce six values for matched classical or quantum heads. The diagram gives the full route; the following pages explain the parameters of each component.

The saved diagram is schematic. Where older diagram text conflicts with enhanced configuration, the enhanced settings prevail: dropout is 0.2 and the VQC uses three variational layers with trainable input calibration. The circuit is simulated rather than executed on quantum hardware.''',figures=[generated('pipeline.png',380,'Figure 1. Complete processing architecture redrawn from the enhanced configuration. Both encoders share head types but learn separate representations.')])

    use(8,'3.1 Dataset Description and Class Coverage')
    p[-1]['text']=p[-1]['text'].replace('archive as supplied','archive as supplied')+'\n\nThe source is the public activities of daily livings dataset attributed to Zia and Khan [13]. No raw dataset was acquired for this revision. The inventory is taken from the saved manifest, rather than inferred from the names of the model outputs.'

    add('3.2 Preprocessing and Motion Artefact Suppression', '''The WOSG front end follows wavelet decomposition, SG smoothing of the approximation band, artefact subtraction and inverse reconstruction [1,14,16]. The implementation uses db4, seven levels and symmetric boundaries. SG window length and polynomial order are chosen per recording by a label free proxy objective balancing low frequency suppression against in band preservation.

These choices are implementation assumptions. They should not be presented as an exact recovery of every unpublished parameter in the reference method. The saved audit reports substantial low frequency attenuation, but suppression alone does not prove preservation of all informative neural content. Filtering is applied to the complete recording and is therefore an offline operation.

The repository examples below show the raw and filtered signal in both classes. Their amplitudes and visible transients are descriptive examples; they do not establish a diagnostic pattern shared by all recordings.''',figures=[figure('raw_vs_filtered.png',250,'Figure 2. Saved raw and WOSG filtered examples for healthy and epilepsy labelled recordings. Source: complete enhanced experiment.')])

    add('3.3 Gaussian Window Stockwell Transform', '''The Stockwell representation localises frequency content over time using a frequency dependent Gaussian window [15]. Each complete EEG window contains 2,560 samples. The implementation evaluates 225 voices from 0.5 to 50 Hz, yielding a frequency by time matrix. Lower frequencies have broader temporal support than higher frequencies.

In continuous form, S(tau,f) is the integral of x(t) g(t-tau,f) exp(-j 2 pi f t), with g(u,f) = |f| exp(-f squared u squared / 2) / sqrt(2 pi). The project uses magnitude features and does not retain the complete transform phase. Fractional frequency shifts are handled explicitly rather than rounding every voice to a DFT bin.

The saved numerical check gives about 1.58 times 10 to the power minus 15 maximum discrepancy against a direct integer frequency definition. A 10 Hz synthetic sinusoid is localised near 10 Hz. These checks support transform consistency, not clinical classification validity.''',figures=[figure('gwst_healthy.png',175,'Figure 3. Saved healthy example with filtered waveform and GWST magnitude.'),figure('gwst_epilepsy.png',175,'Figure 4. Saved epilepsy labelled example. Frequency structure is illustrative and is not an event annotation.')])

    add('3.4 Handcrafted Features and Baseline Models', '''For each frequency row, L1(f) is the sum over time of the GWST magnitude. Shannon entropy is minus the sum of p(b) log2 p(b) over ten equal width histogram bins, with zero probability terms set to zero. Concatenating 225 L1 values and 225 entropy values gives a 450 dimensional vector [1]. Entropy measures also have an established role in the supplied focal EEG study [10], although its task and decomposition differ.

Random forest E1 uses an ensemble of decision trees [17]. Its validation grid spans tree counts 100, 300 and 500; minimum leaf sizes 1, 2, 3 and 5; and maximum depths unrestricted, 4, 6 and 10. The ensemble models nonlinear feature interactions without a temporal neural encoder.

SVM E2 uses scaled handcrafted inputs with linear or RBF kernels and C in 0.1, 1, 10 and 100 [18]. The kernel compares feature vectors rather than explicitly learning temporal token relationships. MI selected RF E3 first ranks or selects training features, with k in 10, 25, 50, 100, 150 and 225, and then fits RF. Information based estimation motivates the selector [19]; the software implementation is scikit learn [27].

Scaling, selection and fitting use training data, with validation loss selecting the recorded configuration. These baselines differ from quantum heads in both representation and fitting. They compare complete pipelines. The matched six dimensional heads provide the more specific classifier control.''',table=(['Model','Input','Decision function'],[['E1 RF','450 summaries','Tree ensemble'],['E2 SVM','450 scaled summaries','Linear or RBF margin'],['E3 MI RF','Selected summaries','Feature selection then forest'],['Temporal heads','6 learned values','Matched head comparison']]))

    add('3.5 Transformer Encoder Architecture', '''A GWST magnitude window is converted to log(1 plus magnitude divided by a0), where a0 is estimated from training windows. Mean pooling over 40 samples yields 64 tokens with 225 frequencies each. Per frequency standardisation uses training statistics. A 225 to 32 linear layer supplies the token width.

The Transformer follows attention based sequence modelling [20], adapted to EEG tokens. Sinusoidal positions identify token order. Two pre normalised blocks each contain four head self attention, a residual connection and a feedforward map 32 to 64 to 32 with GELU. Dropout is 0.2 in the enhanced configuration [26]. Layer normalisation stabilises the token pathway [23].

For each head, attention uses softmax(Q K transpose divided by sqrt(d_k)) V. This allows a token to combine information from other time positions. Final layer normalisation and learned temporal attention pooling yield 32 values. A second normalisation, linear 32 to 6 projection and tanh produce a six dimensional bounded embedding. The encoder has 25,734 parameters including projection and bottleneck.

Encoder pretraining uses a classical MLP objective. Frozen head comparisons subsequently keep this embedding fixed. This ensures common inputs while leaving the possibility that the representation favours the pretraining head.''',figures=[generated('transformer.png',225,'Figure 5. Enhanced Transformer architecture with explicit tensor sizes and residual block structure.')])

    add('3.6 Bidirectional LSTM Encoder Architecture', '''The Bi LSTM receives the same 64 by 225 standardised token representation and the same 225 to 32 input projection. LSTM gating maintains a state through the token sequence [21]. A bidirectional construction processes both temporal directions [22], so the representation can use context before and after a token within the stored window.

The implementation has one recurrent layer with 16 hidden units per direction. The forward and backward outputs concatenate to 32 values at each of 64 time positions. Dropout 0.2 is applied after the recurrent output, followed by temporal attention pooling. LayerNorm, a 32 to 6 linear map and tanh create the shared bottleneck. The complete encoder has 14,982 parameters.

In the recurrent cell, input, forget and output gates control updates to the memory state. The cell state combines retained previous memory with a gated candidate update; the hidden output uses the output gate and a bounded transformation of that state. This mechanism differs from Transformer self attention, which combines tokens directly rather than propagating a recurrent state.

Both encoders are offline within a complete five second window. Bidirectionality does not support a zero look ahead streaming claim. The two encoders also learn different embeddings, so a cross encoder comparison includes representation differences as well as head behaviour.''',figures=[generated('bilstm.png',225,'Figure 6. Bi LSTM architecture. The two recurrent directions are concatenated before pooling and the six dimensional projection.')])

    use(14,'3.7 Variational Quantum Circuit Architecture',table=False)
    p[-1]['text']=p[-1]['text'].split('\n\nThe measured feature')[0]
    p[-1]['text']=p[-1]['text'].replace('Some generated text labels still mention two layers or fixed input angles, and the inventory dictionary key contains 2layers. The saved configuration, actual tensor counts and current implementation support three layers with calibration. The prose labels should not override those artifacts.','The enhanced configuration and total parameter count support three layers with calibration; older two layer labels in generated artifacts are superseded here.')
    p[-1]['figures']=[generated('vqc.png',170,'Figure 7. Corrected enhanced VQC sequence. Six qubits, three variational layers, calibrated angle input and six Pauli Z expectations. No CNOT controls omit the ring only.')]

    add('3.8 Classical Heads Fine Tuning and Augmentation', '''The linear head computes one logit from six embedding values and has seven parameters. The MLP applies Linear 6 to 6, tanh and Linear 6 to 1, with 49 parameters. The RBF SVM uses the same embedding with C in 0.1, 1, 10 and 100 and gamma in scale, 0.01, 0.1, 1 and 10. The VQC has 55 parameters including 12 input calibration values and seven readout values. E4 to E7 use Transformer embeddings; E8 to E11 use Bi LSTM embeddings. E12T and E12B remove the CNOT ring.

Frozen fitting changes only the selected head. Fine tuned variants update encoder and head jointly. The saved optimiser is AdamW [24], an adaptive moment method with decoupled weight decay; Adam supplies the underlying moment adaptation [25]. Maximum budgets are 120 encoder, 160 head and 120 fine tuning epochs with early stopping. Models are implemented using PyTorch [28], scikit learn [27] and PennyLane [29]. No fits are repeated for this revision.

The later archive also compares unaugmented and waveform augmented training. Positive class windows receive small amplitude, noise, drift and shift perturbations. The quick study instead intends MixUp [30], which forms convex combinations of inputs and labels. Source inspection shows no active MixUp application in the recorded base script, so those identical quick outputs do not establish augmentation efficacy. This differs from the waveform archive with logged generated samples and changed results.

The circuit can be differentiated through the simulation, but nonzero gradient checks do not demonstrate a superior optimum. Neither head size nor successful optimisation is sufficient to establish a predictive or computational advantage.''',table=(['Model family','Training changes','Interpretation'],[['Frozen heads','Head only','Same representation control'],['Fine tuned heads','Encoder and head','Adapted complete pipeline'],['Waveform AUG models','Training signals','Within archive intervention'],['Quick MixUp labels','No active path shown','Inconclusive intervention']]))

    add('3.9 Evaluation Protocol and Data Integrity', '''The main complete enhanced run uses three seeds and five outer recording grouped folds. Training data determine feature scales, encoder parameters and feature selection. Validation determines hyperparameters, early stopping and thresholds. Test windows are aggregated to a mean probability per recording, then classified using the fixed validation threshold. Three seed averages are summaries of repeated use of the same dataset, not independent new cohorts.

Accuracy, balanced accuracy, sensitivity, specificity, macro F1, ROC AUC and MCC are reported. Balanced accuracy is the mean of sensitivity and specificity. The primary table pools held out recordings within each seed, then averages seed metrics. Paired bootstrap intervals resample the same recording indices across heads; fold variability is a separate summary. An interval containing zero is not proof of equivalence.

A content audit identifies three healthy idle sitting files with the same signal hash. Their group crosses partitions in 14 of 15 seed and fold combinations and includes both train and test in nine. Thus recording ID grouping prevents ordinary within file window leakage, but not all identical content leakage. Ninety files represent 88 distinct hashed sequences, not 90 verified participants. Participant identifiers are unavailable.

The shared activity subset has 77 files. Four other activities are healthy only, creating class correlated activity coverage. Shared activity metrics restrict the saved test predictions; they do not retrain a separate 77 file model. All results remain descriptive of the archived protocol, with these limitations applying equally to classical and quantum rows.

Evidence paths are retained in the editable source and figure manifest. The complete enhanced run is outputs/experiment_20261116_143634; the separate waveform archive is outputs/experiment_20261116_202913. Quick MixUp runs reside under outputs_gwst_vqc_ablation. This separation is maintained in every comparison.''')

    use(18,'4 Results and Discussion')
    p[-1]['text']=p[-1]['text'].replace('Table 1','Table 1')
    add('4.1 Handcrafted Model Results', '''The following model panels report five recording metrics for every handcrafted baseline. All values are taken from the complete enhanced run and averaged across three seeds. The bars use a common zero to 100 percent scale; they are not new evaluations.

RF reaches 80.37% accuracy and 76.11% balanced accuracy. SVM has higher accuracy at 82.22%, but sensitivity is only 58.89%. MI selected RF is weaker on balanced accuracy at 71.67%. These differences show why a single accuracy ranking hides important class specific errors. They also establish a meaningful classical starting point before the learned embeddings are considered.''',figures=[generated('handcrafted_metrics.png',415,'Figure 8. Individual model panels for E1 RF, E2 SVM and E3 MI selected RF. Metrics are accuracy, balanced accuracy, sensitivity, specificity and macro F1.')])

    add('4.2 Transformer Model Results', '''All Transformer head variants receive the same frozen six dimensional representation within each fold and seed. Linear and MLP balanced accuracy is 81.39%; VQC achieves 78.61%. The VQC accuracy gap relative to MLP is 2.59 percentage points, while its balanced accuracy is 0.56 points above RBF SVM.

The strongest classical control must remain in the discussion. Comparing VQC only against a weaker baseline would exaggerate benefit. The no CNOT circuit improves the circuit point estimate, so the entangling ring is not the demonstrated source of the best performance.''',figures=[generated('transformer_metrics.png',440,'Figure 9. Model specific panels for E4 linear, E5 MLP, E6 RBF SVM, E7 VQC and E12T no CNOT. Same axes and three seed recording metrics.')])

    add('4.3 Bi LSTM Model Results', '''Bi LSTM VQC obtains 75.93% accuracy and 75.56% balanced accuracy. Its sensitivity equals the Bi LSTM linear head at 74.44%, but specificity falls from 84.44% to 76.67%. The lower quantum result in this comparison is therefore driven by more false positive healthy classifications rather than lower positive class recall.

The Bi LSTM MLP and RBF SVM also exceed VQC on balanced accuracy. The no CNOT version improves the quantum point estimate but remains below linear. These findings show that the outcome depends on the encoder and should not be generalised from the Transformer branch alone.''',figures=[generated('bilstm_metrics.png',440,'Figure 10. Model specific panels for E8 linear, E9 MLP, E10 RBF SVM, E11 VQC and E12B no CNOT. Data: complete enhanced archive.')])

    use(21,'4.4 Entanglement Ablation',table=False,chart=True)
    add('4.5 Fine Tuned Model Results', '''Fine tuning allows the representation to adapt to its head and is a separate experiment from frozen comparison. Transformer VQC reaches 82.96% accuracy and 79.72% balanced accuracy, improving over its frozen values. Transformer MLP still has a higher balanced accuracy point estimate of 81.67% and accuracy of 84.44%.

Bi LSTM VQC reaches 78.06% balanced accuracy, equal to the fine tuned linear point estimate and below MLP at 79.17%. These improvements support studying encoder and head compatibility, but do not establish a quantum advantage. The six panels below include every fine tuned model in the complete archive.''',figures=[generated('finetuned_metrics.png',440,'Figure 11. Individual panels for all six fine tuned models. Encoder adaptation is included, so these results should not be presented as isolated head effects.')])

    add('4.6 Saved Global Model Comparison', '''The original repository figures summarise all 13 frozen or classical models and all six fine tuned models. The x axis is recording balanced accuracy, with archived 95% bootstrap whiskers. These are the complete enhanced experiment figures, included without changing their numerical content.

Uncertainty overlaps across several heads. The paired Transformer VQC minus MLP difference is minus 2.78 percentage points with interval minus 6.82 to plus 1.80. That contrast does not establish superiority or equivalence. Duplicate content and unknown participant clustering also limit the independence assumptions behind the saved intervals.''',figures=[figure('model_comparison.png',300,'Figure 12. Original saved frozen and classical comparison with recording bootstrap intervals.'),figure('model_comparison_finetuned.png',165,'Figure 13. Original saved comparison of the six fine tuned models. These are three seed summaries, not a separate dataset.')])

    add('4.7 ROC Curves and Ranking Performance', '''ROC curves compare score ranking over possible thresholds. The saved figure below uses seed zero pooled outer test recordings. It must not be mistaken for the three seed mean AUC in the primary table. Both panels include classical baselines and the matched heads of one encoder family.

The three seed Transformer VQC ROC AUC is 0.8919 compared with 0.9022 for MLP. Similar ranking quality can coexist with different binary accuracy because thresholds and calibration affect the operating point. Test labels must not be used to choose a more favourable threshold after observing these curves.''',figures=[figure('roc_curves.png',235,'Figure 14. Original seed zero ROC curves for Transformer and Bi LSTM branches.'),figure('recording_level_results.png',260,'Figure 15. Original seed zero recording probabilities for selected classical and quantum models. Scores are diagnostic displays, not three seed aggregate predictions.')])

    add('4.8 Recording Confusion Matrices', '''The recording confusion matrix grid provides an error count view for every frozen or handcrafted model. It is the saved seed zero result pooled over outer test folds. Each matrix contains 60 healthy and 30 epilepsy labelled test recordings. Rows are true labels and columns are predicted labels.

Comparing the false positive and false negative cells reveals why total accuracy and balanced accuracy can favour different models. A classifier with high specificity may lose sensitivity under the class imbalance. The grid is not a new confusion matrix built by pooling three repetitions of each recording.

The scalar metrics in Table 1 are three seed means, so a count from one matrix need not equal the count implied by rounding a mean percentage. The distinction is retained to avoid treating repeated seeds as independent patients.''',figures=[figure('confusion_matrix.png',330,'Figure 16. Original recording confusion matrices for all 13 frozen or handcrafted models at seed zero. The archive labels the pooled folds and validation selected threshold.')])

    add('4.9 Window Confusion Matrices', '''The window confusion grid uses the same saved seed zero experiment at a different observational level. Each matrix covers 360 windows, with four windows belonging to each recording. These are correlated segments and cannot be counted as 360 independent participants.

Recording aggregation can improve the final decision by averaging imperfect window probabilities. Consequently, window and recording accuracy are related but are not interchangeable endpoints. The report treats recording balanced accuracy as primary and the window plots as diagnostics of how predictions vary within a recording.

A stronger clinical evaluation would require a task definition with event annotations or patient outcomes. The current window labels inherit the recording class and are not independently verified seizure onset annotations.''',figures=[figure('confusion_matrix_window.png',330,'Figure 17. Original seed zero window level confusion matrices for all 13 frozen or handcrafted models. These plots are secondary to recording level evaluation.')])

    add('4.10 Encoder Training Curves', '''The repository stores encoder pretraining loss curves and validation balanced accuracy traces. Each encoder figure summarises 15 runs from three seeds and five folds. These are historical curves: the revision did not restart training or extend any epoch budget.

Training loss generally declines more consistently than validation loss. A separation between them is compatible with finite sample overfitting or model selection variability, but the plots alone do not identify the cause of the VQC gap. The curves describe encoder pretraining, not a separate per head training trajectory for every downstream classifier.

Early stopping selects a checkpoint from validation behaviour. A maximum epoch setting is not the number of epochs used for every fit. Per fit metadata in training_summary.csv should be consulted for an exact accounting.''',figures=[figure('training_loss_transformer.png',180,'Figure 18. Saved Transformer encoder pretraining loss and validation balanced accuracy across 15 runs.'),figure('training_loss_bilstm.png',180,'Figure 19. Saved Bi LSTM encoder pretraining traces. Classical MLP pretraining precedes the frozen head comparisons.')])

    add('4.11 Results by Physical Activity', '''The original figure reports recording accuracy and balanced accuracy by activity or activity group. Per activity samples are small, and four activities are healthy only. Accuracy on those activities is a specificity observation rather than an estimate of epilepsy detection within that activity.

Transformer VQC performs strongly on walking but has weaker point estimates for some stationary conditions. Neither a selected perfect activity score nor a group average demonstrates broad activity invariance. The shared activity subset is a useful sensitivity analysis, but it reuses saved predictions from the original trained models.

The all activity and paired activity populations also differ in prevalence and composition. Comparisons should therefore show both the activity count limitation and the distinction between accuracy and balanced accuracy.''',figures=[figure('activity_comparison.png',310,'Figure 20. Original activity and activity group comparison from the complete enhanced run. Top: accuracy. Bottom: balanced accuracy. Healthy only activities do not support within activity sensitivity.')])

    add('4.12 Transfer to an Unseen Activity', '''Leave one activity out evaluation holds out an eligible activity for testing and chooses validation recordings only from other activities. It asks a different question from random recording grouped folds: whether the model transfers to an activity condition absent during fitting.

Transformer VQC balanced accuracy varies from 90.00% for walking to about 38.89% for sitting and 45.56% for running. Bi LSTM VQC reaches 83.33% for jogging but about 33.33% for laying. These means are unstable because each held out activity has few observations.

The plot therefore identifies a generalisation boundary, rather than uniform activity robustness. It also must not be confused with the base paper's activity specific leave one out validation, where the held out unit and training population differ.''',figures=[figure('activity_holdout_comparison.png',310,'Figure 21. Original leave one activity out comparison. Top: accuracy. Bottom: balanced accuracy across the eight activities shared by both classes.')])

    add('4.13 Noise Robustness Results', '''The saved stress tests add Gaussian noise, drift, EMG like or ocular like corruption to test signals at fixed SNRs while keeping trained models and thresholds fixed. The SNR is referenced to raw signal power; filtering can change the effective corruption after preprocessing. Synthetic artefacts are proxies, not newly recorded movement artefacts.

At 5 dB, averaging the four recording level corruption types gives Transformer VQC balanced accuracy of 66.88%, compared with 68.33% for MLP. VQC drops by 11.74 points from clean, while MLP drops by 13.06. A smaller drop from a lower clean starting point is not superior absolute performance.

The original plots include the wider model set and multiple SNRs. They support a defined synthetic perturbation comparison; they do not establish clinical robustness or explain errors as quantum hardware noise.''',figures=[figure('noise_robustness_balanced_accuracy.png',145,'Figure 22. Original recording balanced accuracy under four synthetic corruption types. SNR and corruption definitions are fixed by the archived configuration.'),figure('noise_model_comparison.png',220,'Figure 23. Original mean change across synthetic conditions by model. This is a descriptive aggregate, not an independent robustness test cohort.')])

    add('4.14 Waveform Augmentation and MixUp Audit', '''The later archive compares its own baseline with training only waveform perturbations of positive class windows. Bi LSTM VQC balanced accuracy rises from 77.50% to 82.50%; sensitivity rises from 73.33% to 84.44% while specificity falls slightly. Transformer VQC improves more modestly from 78.06% to 79.44% balanced accuracy.

The figure covers all 19 base model identities and their AUG counterparts in that archive. It must not be subtracted from the earlier complete run because the later baseline differs. Only positive class training windows are augmented, so increased exposure to that class may contribute alongside waveform invariance.

The separate quick MixUp pair has byte identical metric files and no demonstrated MixUp application in the base training path. It is not evidence that augmentation has no effect. This intervention validity issue remains distinct from the waveform result.''',figures=[generated('augmentation_all.png',370,'Figure 24. Within archive baseline versus waveform augmentation balanced accuracy for all 19 model identities. Source: experiment_20261116_202913. The final narrative report is absent in that archive.')])

    add('4.15 Interpretation of the Quantum Results', '''The evidence does not demonstrate quantum superiority. In the main complete run, the strongest frozen classical head exceeds VQC. The no CNOT point estimates improve, and the seven parameter linear head is already strong on the learned representation. The most defensible conclusion is that the implemented quantum function family adds no established benefit over the strongest controls under this protocol.

Several mechanisms are plausible but unproven. The embedding was pretrained with an MLP objective, the circuit encodes the input once and the topology may not match the relevant decision boundary. Small validation sets and threshold choices also affect class specific errors. Ideal simulation excludes physical gate noise as a measured explanation. Nonzero saved gradient checks exclude a simple broken gradient path but do not diagnose or rule out all optimisation difficulties.

Parameter and timing accounting also matters. VQC has 55 head parameters, versus 49 for MLP and seven for linear. Mean selected Transformer head fit times are approximately 19.86 seconds for VQC, 0.41 for MLP and 0.32 for linear. The common encoder has 25,734 parameters. These observations do not support a smaller or faster complete quantum pipeline.

The earlier full run, enhanced run and later augmentation baseline also differ numerically. They are sensitivity evidence, not independent cohorts or one factor causal ablations. Broadly overlapping paired intervals do not establish equivalence, and duplicated signals restrict the meaning of every saved confidence interval.

Lower quantum accuracy can still yield a useful research result when the objective is to test a controlled hypothesis. The contribution is a documented benchmark, a negative entanglement finding and a clear boundary on claims. Literature on benchmarking, data dependent advantage and generalisation supports asking these questions [2,4,5], while the actual answer must come from the present controls and limitations.''')

    add('5 Comparison with the Base Paper', '''The base paper is Dash et al [1]. The table separates published measurements from locally saved measurements and identifies their protocols. The wearable RF value of 90.74% and the paper's multilayer LSTM values do not use the same evaluation unit as this project's pooled recording predictions.

The local RF accuracy is 80.37%, a descriptive difference of minus 10.37 percentage points from the published RF hold out value. This subtraction is arithmetic, not an estimate of improvement or degradation under matched conditions. The populations, frame counts, splitting, tuning and aggregation differ. Likewise, the current fine tuned MLP score cannot establish superiority over the paper's ten fold LSTM result.

The reference paper also evaluates other datasets. Its resting state or multichannel seizure results must not be used as wearable baselines. The present comparison is restricted to the wearable context and retains the original authors' terminology for their protocols.''',table=(['Study and model','Accuracy %','Evaluation description'],[['Base paper RF','90.74','Wearable frame based hold out'],['Base paper multilayer LSTM','87.04','Wearable hold out'],['Base paper multilayer LSTM','74.44','Wearable ten fold CV mean'],['Current GWST RF E1','80.37','Recording grouped CV, 3 seeds'],['Current Transformer MLP E5','83.70','Frozen head, recording metrics'],['Current Transformer VQC E7','81.11','Frozen head, recording metrics'],['Current fine tuned T MLP','84.44','End to end, recording metrics'],['Current fine tuned T VQC','82.96','End to end, recording metrics']]),figures=[generated('base_comparison.png',190,'Figure 25. Published and local accuracy values grouped by source. Different protocols are explicitly separated; bars do not form a matched performance ranking.')])

    add('5.1 Protocol Differences and Contribution', '''The common methodological basis is clear: wearable EEG, WOSG motivated preprocessing, five second windows and L1 plus entropy summaries derived from GWST. The extension is temporal token modelling with independent Transformer and Bi LSTM encoders, followed by matched classical and simulated quantum heads. The ablations, recording aggregation and saved paired comparisons provide additional analysis.

The paper reports 540 five second wearable frames and 45 minutes, while the archived 90 approximately 20 second files provide 360 non overlapping windows and about 30 minutes. The supplied artifacts do not resolve this difference. Overlap or a different source subset is possible but unverified. The local use of 60 healthy and 30 positive files also differs from a statement in the paper about selecting 30 files per class.

Recording grouping is explicit in the current protocol. It is not sufficient for content independence because duplicated waveforms cross partitions; the reference description does not permit a verified recording grouping claim either. These are distinct limitations, and the present duplicate finding is not proof that the published study had the same problem.

The contribution should therefore be stated as an extension and critical benchmark, not an exact replication or accuracy improvement. The quantum branch establishes feasible differentiable integration, while its strongest practical comparator remains classical. Further work should first fix content grouping and obtain participant identifiers, then compare limited architecture changes under the same validation plan.''',table=(['Aspect','Base paper','Current saved study'],[['Representation','GWST L1 and entropy','Same summaries plus tokens'],['Temporal model','Multilayer LSTM variants','Transformer and Bi LSTM'],['Quantum head','Absent','6 qubit VQC and no CNOT'],['Primary unit','Published frame protocols','Recording probability aggregation'],['Wearable windows','540 reported','360 archived'],['Robustness','Published activity studies','Activity holdout and synthetic noise'],['Fair head control','Different classifier families','Same 6 dimensional embeddings']]))

    use(36,'6 Conclusion')
    p[-1]['text']+='\n\nThe contribution relative to the base paper is an expanded architectural and evaluation study. The published accuracy values are contextual references under different protocols, and no superiority over that paper is claimed. Future validation should prioritise independent content and participants before greater circuit complexity.'

    refs=base_refs+[
        ('[13]','S. Zia and A. Nawaz Khan. Activities of daily livings using a portable EEG headset. IEEE DataPort dataset, 2021.','https://doi.org/10.21227/mtwx-p951'),
        ('[14]','P. Gajbhiye, N. Mingchinda, W. Chen, S. C. Mukhopadhyay, T. Wilaiprasitporn and R. K. Tripathy. Wavelet domain optimized Savitzky-Golay filter for the removal of motion artifacts from EEG recordings. IEEE Transactions on Instrumentation and Measurement 70, 4002111, 2021.','https://doi.org/10.1109/TIM.2020.3041099'),
        ('[15]','R. G. Stockwell, L. Mansinha and R. P. Lowe. Localization of the complex spectrum: the S transform. IEEE Transactions on Signal Processing 44, 998-1001, 1996.','https://doi.org/10.1109/78.492555'),
        ('[16]','A. Savitzky and M. J. E. Golay. Smoothing and differentiation of data by simplified least squares procedures. Analytical Chemistry 36, 1627-1639, 1964.','https://doi.org/10.1021/ac60214a047'),
        ('[17]','L. Breiman. Random forests. Machine Learning 45, 5-32, 2001.','https://doi.org/10.1023/A:1010933404324'),
        ('[18]','C. Cortes and V. Vapnik. Support-vector networks. Machine Learning 20, 273-297, 1995.','https://doi.org/10.1007/BF00994018'),
        ('[19]','A. Kraskov, H. Stogbauer and P. Grassberger. Estimating mutual information. Physical Review E 69, 066138, 2004.','https://doi.org/10.1103/PhysRevE.69.066138'),
        ('[20]','A. Vaswani et al. Attention is all you need. Advances in Neural Information Processing Systems 30, 2017.','https://arxiv.org/abs/1706.03762'),
        ('[21]','S. Hochreiter and J. Schmidhuber. Long short-term memory. Neural Computation 9, 1735-1780, 1997.','https://doi.org/10.1162/neco.1997.9.8.1735'),
        ('[22]','M. Schuster and K. K. Paliwal. Bidirectional recurrent neural networks. IEEE Transactions on Signal Processing 45, 2673-2681, 1997.','https://doi.org/10.1109/78.650093'),
        ('[23]','J. L. Ba, J. R. Kiros and G. E. Hinton. Layer normalization. arXiv:1607.06450, 2016.','https://arxiv.org/abs/1607.06450'),
        ('[24]','I. Loshchilov and F. Hutter. Decoupled weight decay regularization. International Conference on Learning Representations, 2019.','https://arxiv.org/abs/1711.05101'),
        ('[25]','D. P. Kingma and J. Ba. Adam: A method for stochastic optimization. International Conference on Learning Representations, 2015.','https://arxiv.org/abs/1412.6980'),
        ('[26]','N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov. Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine Learning Research 15, 1929-1958, 2014.','https://jmlr.org/papers/v15/srivastava14a.html'),
        ('[27]','F. Pedregosa et al. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research 12, 2825-2830, 2011.','https://jmlr.org/papers/v12/pedregosa11a.html'),
        ('[28]','A. Paszke et al. PyTorch: An imperative style, high-performance deep learning library. Advances in Neural Information Processing Systems 32, 2019.','https://arxiv.org/abs/1912.01703'),
        ('[29]','V. Bergholm et al. PennyLane: Automatic differentiation of hybrid quantum-classical computations. arXiv:1811.04968, 2018, revised 2022.','https://arxiv.org/abs/1811.04968'),
        ('[30]','H. Zhang, M. Cisse, Y. N. Dauphin and D. Lopez-Paz. mixup: Beyond empirical risk minimization. International Conference on Learning Representations, 2018.','https://arxiv.org/abs/1710.09412')]
    # Keep locally supplied papers, replacing long local paths with checked DOI links where available.
    refs[10]=(refs[10][0],refs[10][1],'https://doi.org/10.3390/app7040385')
    for k in range(3):
        block=refs[k*10:(k+1)*10]
        add('References' if k==0 else 'References Continued','\n\n'.join(a+' '+b+'\n'+c for a,b,c in block))
    assert len(p)==40,len(p)
    assert len(refs)==30
    (root/'report_work/references.json').write_text(json.dumps([{'id':a,'reference':b,'url':c} for a,b,c in refs],indent=2))
    for item in p:
        # Source markers P1-P6 belong in the evidence register rather than unresolved body citations.
        for tag in [' [P1, P5]',' [P1, P4]',' [P1-P5]',' [P1]',' [P2]',' [P3]',' [P4]',' [P5]',' [P6]']:
            item['text']=item['text'].replace(tag,'')
    return p
