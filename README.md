# Flask Transcriber

Local audio-to-text web app using OpenAI Whisper (small) with Flask. Upload audio,
transcribe it locally, edit the note, and download the text.

## Features
- Upload audio files and transcribe with Whisper (offline, local model).
- Store transcriptions as notes in SQLite.
- View, edit, delete, and download notes.

## Tech
Flask, Transformers, Whisper, PyTorch, Librosa, SQLite.

## Requirements
- Python 3.9+ (3.10+ recommended)
- Disk space for the model (hundreds of MB)
- Optional: CUDA 11.8 for GPU acceleration
- Optional: FFmpeg for broader audio format support

## Quickstart (Windows)
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python download_model.py
python app.py
```

Open `http://127.0.0.1:8000` in your browser.

## CPU-only setup
If you do not have CUDA 11.8, install CPU wheels for torch first, then install
the rest of the dependencies:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install librosa transformers soundfile werkzeug flask "numpy<2"
```

## Usage
1. Open the home page.
2. Upload an audio file (wav, mp3, ogg, m4a, webm).
3. The transcription is saved as a note.
4. Open a note to edit or download it as a `.txt`.

## Project layout
```
app.py              App entrypoint
transcriber/        Flask app package (config, db, routes, transcription)
download_model.py   Downloads Whisper model into ./model
model/              Local Whisper model files
uploads/            Temporary uploaded files
notes.db            SQLite database (notes)
templates/          HTML templates (layouts, pages, partials)
static/             CSS and JS assets
```

## Configuration
Edit these in `transcriber/config.py`:
- `ALLOWED_EXTENSIONS`
- `UPLOAD_FOLDER`
- `MODEL_DIR`
- `MAX_CHUNK_SECONDS`
- `PRELOAD_MODEL`

## Notes
- For best results, use clear audio with minimal background noise.
- If MP3/OGG/M4A fails to load, install FFmpeg and try again.
