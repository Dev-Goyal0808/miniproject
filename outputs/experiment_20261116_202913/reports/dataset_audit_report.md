# Dataset audit report

Data source: `ADLs using a Portable EEG Headset.zip` (zip). Generated automatically by `hybrid_quantum_eeg_epilepsy.py`.

## 1. Inventory

| Item | Documented | Found |
|---|---|---|
| CSV recordings | 90 | 90 |
| Healthy recordings | 60 | 60 |
| Epilepsy recordings | 30 | 30 |
| Samples per recording | 10240 | {'10241': 90} |
| Recordings excluded from modelling | - | 0 |

Recordings excluded (with reasons): none

## 2. Activity coverage (from normalised file names)

| activity | Epileptic Patients | Healthy Individuals | both_classes |
|---|---|---|---|
| cooking | 0 | 3 | no |
| desk work | 3 | 7 | yes |
| idle sitting | 3 | 4 | yes |
| jogging | 3 | 6 | yes |
| jumping | 0 | 5 | no |
| laying | 3 | 2 | yes |
| running | 3 | 5 | yes |
| sitting | 3 | 7 | yes |
| stairs | 6 | 6 | yes |
| standing | 0 | 2 | no |
| walking | 6 | 10 | yes |
| watching tv | 0 | 3 | no |

Activities present in both classes (used for activity-transfer experiments): **desk work, idle sitting, jogging, laying, running, sitting, stairs, walking**.
Healthy-only activities (never used in binary activity-transfer experiments): cooking, jumping, standing, watching tv.

Unknown/unnormalised activity names: none.

ReadMe code (00/01/02) vs name-based group mismatches: 0.

## 3. Length discrepancy (10,241 vs documented 10,240 samples)

- Length histogram: {'10241': 90}
- All recordings share the same length: **True**; excess over documentation: **1 sample(s)**.
- Header rows: 0 files; files whose last sample equals the previous sample: 2; files whose first two samples are equal: 46.
- Formatting quirk: 1 file(s) carry trailing commas on every row: ['Healthy Individuals/02_jumping1.csv']

**Interpretation (inference, not proof).** Every recording has 10241 numeric rows (documented: 10240 = 20 s x 512 Hz). The excess is exactly 1 sample(s) in every file, with no header row, no extra column and no malformed row. This systematic pattern is consistent with INCLUSIVE ENDPOINT SAMPLING (t = 0 ... 20 s gives 20*512+1 samples) or a single extra sample logged at acquisition start/stop. It is NOT a formatting artefact (a trailing newline is counted separately and only 1 file(s) carry a trailing-comma formatting quirk). The raw files alone cannot prove which acquisition mechanism produced the sample; this is an inference, not a verified fact.

**Policy used:** `keep_filter_drop_incomplete`. All samples are filtered; non-overlapping 5 s windowing yields floor(N/2560) complete windows; the trailing incomplete segment (N mod 2560 samples) is reported per recording and excluded.

With non-overlapping 5 s windows (2,560 samples) a 10,241-sample recording yields 4 complete windows and 1 unused trailing sample (logged per recording in `data/recording_metadata.csv`, column `leftover_samples`). Nothing is silently truncated: the policy is configurable (`data.length_policy`).

## 4. Signal-quality checks

- Global amplitude range: [-15.012, 9.006]; median per-recording std 1.337. Values are quantised (see manifest n_unique) and many recordings touch the global min/max; saturation/clipping of the dry-electrode headset is likely (fraction per recording in manifest column saturation_fraction_global_extremes).
- Constant recordings: none
- Duplicate recordings (identical samples): [['H_00_idle_sitting2', 'H_00_idle_sitting1'], ['H_00_idle_sitting3', 'H_00_idle_sitting1']]
- Recordings with unusual standard deviation (|robust z| > 6): none
- Saturation fraction (samples at the global min/max): median 0.0000, max 0.0361 (per recording in the manifest).

## 5. Participant identity

The archive provides NO participant identifiers. Numbers in file names are recording counters per activity and are NOT interpreted as subject IDs. Recording-level grouping prevents window leakage but multiple recordings may come from the same person, so participant-independent generalisation cannot be claimed.

## 6. Files

- `config/dataset_manifest.csv` - one row per CSV with all audit fields.
- `config/dataset_audit.json` - machine-readable audit.
