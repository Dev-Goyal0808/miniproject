# Local setup

The repository is checked out directly in `X:\AI-Projects\MiniProject`.
The Python environment is `.venv`; select `.venv\Scripts\python.exe` in your editor or notebook kernel picker.

To recreate the environment in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Check the command-line options:

```powershell
.\.venv\Scripts\python.exe hybrid_quantum_eeg_epilepsy.py --help
```

The EEG dataset is not included in the repository. Once you have it, run:

```powershell
.\.venv\Scripts\python.exe hybrid_quantum_eeg_epilepsy.py --profile smoke --data-path "C:\path\to\ADLs using a Portable EEG Headset.zip"
```

The default dataset location is `ADLs using a Portable EEG Headset.zip` in this folder. Alternatively, set `EEG_DATA_PATH` or pass `--data-path`. The preprocessing notebooks have a separate hard-coded `DATA_PATH` that must be updated to your CSV location.

The Python Graphviz package is included; its optional `dot` executable is separate. The scripts use a Matplotlib fallback if `dot` is unavailable. CUDA availability depends on the installed PyTorch build and compatible hardware; CPU execution is supported.

Existing research PDFs and README were preserved. The local `notes.md` was moved into `local-backup-20261117-184133` before the repository copy was installed. The existing README describes the earlier research-planning state; consult the Python scripts and repository outputs for the downloaded implementation.
