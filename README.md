# Flask Transcriber

Local audio-to-text web app using OpenAI Whisper (small) with Flask. Upload audio,
transcribe it locally, edit the note, and download the text.

## Run on Any Windows PC (no Python needed)
This produces a normal desktop-style app (EXE) and can be copied to other PCs.

### 1) Build the app (on your development PC)
```powershell
.\build_windows.ps1
```
This creates:
```
dist\FlaskTranscriber\FlaskTranscriber.exe
```

### 2) Copy to another PC
Copy the entire folder below to the target PC (do not copy only the EXE):
```
dist\FlaskTranscriber\
```
Optional (to keep your notes and uploads):
- Copy `notes.db` into `dist\FlaskTranscriber\`
- Copy the `uploads` folder into `dist\FlaskTranscriber\`

### 3) Run
On the target PC:
- Double-click `FlaskTranscriber.exe`
- The browser should open automatically to `http://127.0.0.1:8000`
- Create a desktop shortcut: Right-click EXE -> Send to -> Desktop (create shortcut)

## CPU-only build (for PCs without NVIDIA GPU)
If the app crashes with CUDA errors on a CPU-only PC, build a CPU version:
```powershell
# Create/activate venv if needed
python -m venv .venv
.\.venv\Scripts\activate

# Install CPU-only PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install the rest
pip install librosa transformers soundfile werkzeug flask "numpy<2" waitress pyinstaller

# Build
pyinstaller --noconsole --onedir --name "FlaskTranscriber" --icon "app.ico" \
  --add-data "templates;templates" --add-data "static;static" --add-data "model;model" launcher.py
```

## Developer quickstart (run from source)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python download_model.py
python app.py
```
Open `http://127.0.0.1:8000` in your browser.

## Features
- Upload audio files and transcribe with Whisper (offline, local model).
- Store transcriptions as notes in SQLite.
- View, edit, delete, and download notes.

## Project layout
```
app.py              App entrypoint (dev)
launcher.py         Packaged app entrypoint (Waitress + auto-open browser)
build_windows.ps1   Windows build script (PyInstaller)
model/              Local Whisper model files
uploads/            Temporary uploaded files
notes.db            SQLite database (notes)
templates/          HTML templates (layouts, pages, partials)
static/             CSS and JS assets
transcriber/        Flask app package (config, db, routes, transcription)
```

## Configuration
Edit these in `transcriber/config.py`:
- `ALLOWED_EXTENSIONS`
- `UPLOAD_FOLDER`
- `MODEL_DIR`
- `MAX_CHUNK_SECONDS`
- `PRELOAD_MODEL`

## Notes
- The model is large (near 1 GB). First run may take time to load.
- If MP3/OGG/M4A fails to load, install FFmpeg and try again.
