# Flask Transcriber

A local, offline audio-to-text web app built with Flask + Whisper (via Hugging Face
Transformers). Upload an audio file (or record from your microphone), transcribe
on your machine, edit, and download notes.

- Runs locally at `http://127.0.0.1:8000`
- Stores notes in SQLite (`notes.db`)
- Saves uploaded audio under `uploads/` (deleted when you delete the note)

## Using the app

1. Start the app (see **Run from source** or **Portable Windows EXE** below).
2. In the browser:
   - **Record**: click Start/Stop (Chrome/Edge will ask for mic permission).
   - **Upload**: choose an audio file and transcribe (shows chunk progress).
   - **Notes**: open a note to edit or download; delete removes its audio too.

Supported extensions are configured in `transcriber/config.py` via
`ALLOWED_EXTENSIONS`.

## Run from source (developer)

Prereqs: Windows + Python 3.11+.

### 1) Create + activate venv

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
```

### 2) Install dependencies

GPU/CUDA (NVIDIA GPU + drivers):
```powershell
pip install -r requirements.txt
```

CPU-only (no CUDA / no NVIDIA GPU):
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install librosa transformers soundfile werkzeug flask "numpy<2" waitress
```

### 3) Download the Whisper model (one-time)

The model is gitignored because it’s large (~1 GB). If `model/` is empty/missing,
download it (requires internet access):

```powershell
python download_model.py
```

### 4) Run

```powershell
python app.py
```

Open `http://127.0.0.1:8000`.

## Portable Windows EXE (no Python on target PC)

Build on your dev machine, then copy the produced folder to any other Windows PC.
Make sure `model/` is populated first (run `python download_model.py` once). The
build scripts create a virtualenv and `pip install` dependencies (internet needed).

### GPU build

```powershell
.\build_windows.ps1
```

Output: `dist\FlaskTranscriber\FlaskTranscriber.exe`

### CPU-only build

```powershell
.\build_windows_cpu.ps1
```

Output: `dist_cpu\FlaskTranscriber\FlaskTranscriber.exe`

### Copy to another PC

Copy the entire folder (not just the `.exe`) to the target PC:
- GPU: `dist\FlaskTranscriber\`
- CPU: `dist_cpu\FlaskTranscriber\`

To keep your data on the target PC, also copy:
- `notes.db`
- `uploads\`

### Run

Double-click `FlaskTranscriber.exe`. It starts a local server and opens your
browser.

Packaged builds auto-exit after a short idle period (defaults to ~2 minutes after
you close the tab). If the app seems “silent”, check `app.log` next to the `.exe`.

## Installer (optional)

Requires Inno Setup 6 installed.

```powershell
.\build_installer.ps1 -Flavor cpu
.\build_installer.ps1 -Flavor gpu
```

Output: `dist_installer\FlaskTranscriber_Setup.exe`

## Configuration

Edit `transcriber/config.py`:
- `ALLOWED_EXTENSIONS`
- `MAX_CHUNK_SECONDS` (audio chunking for Whisper)
- `PRELOAD_MODEL` (load model at startup)
- `IDLE_SHUTDOWN_SECONDS` (packaged app auto-exits when idle; set `0` to disable)
- `UPLOAD_FOLDER`, `DB_PATH`, `MODEL_DIR`

## Troubleshooting

- If MP3/OGG/M4A fails to load, install FFmpeg and try again.
- If you see CUDA errors on a CPU-only PC, use the CPU-only build.
- If port 8000 is in use, stop the other process or change the port in `app.py`
  (dev) / `launcher.py` (packaged).

## Project layout

```
app.py                 App entrypoint (dev)
launcher.py            Packaged app entrypoint (Waitress + auto-open browser)
build_windows.ps1      Windows build script (PyInstaller)
build_windows_cpu.ps1  CPU-only Windows build script (PyInstaller)
build_installer.ps1    Optional Inno Setup installer builder
model/                 Local Whisper model files (gitignored)
uploads/               Uploaded audio files (gitignored)
notes.db               SQLite database (gitignored)
templates/             HTML templates
static/                CSS and JS assets
transcriber/           Flask app package (config, db, routes, transcription)
```
