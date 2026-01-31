import os
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response,
    abort,
)
from werkzeug.utils import secure_filename

import librosa
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

app = Flask(__name__)

DB_PATH = "notes.db"

# ====== Upload config ======
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a", "webm"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ====== Database helpers ======
def get_connection():
    """Create a new database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access: row["content"]
    return conn


def init_db():
    """Create the notes table if it doesn't exist."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


# Make sure the DB + table exist when the app starts
init_db()


# ====== Load Whisper model (local, offline) ======
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_DIR = "model"  # created with download_model.py

print(f"Loading Whisper model from '{MODEL_DIR}' on {DEVICE}...")
processor = WhisperProcessor.from_pretrained(MODEL_DIR)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_DIR).to(DEVICE)
model.eval()
print("Whisper model loaded.")


def transcribe_audio(filepath: str) -> str:
    """
    Transcribe an audio file using Whisper and return the full text.

    We chunk the audio into ~30-second segments because Whisper has
    a limited context window.
    """
    # 1. Load full audio and resample to 16kHz
    audio, sr = librosa.load(filepath, sr=16000)
    if audio.ndim > 1:
        # If stereo, convert to mono
        audio = librosa.to_mono(audio)

    # 2. Define chunk size (in samples)
    max_chunk_seconds = 20  # you can increase to 30 if you like
    chunk_size = max_chunk_seconds * 16000  # 25s * 16000Hz

    total_samples = len(audio)
    if total_samples == 0:
        return ""

    # 3. Split into chunks
    chunks = []
    for start in range(0, total_samples, chunk_size):
        end = min(start + chunk_size, total_samples)
        chunk = audio[start:end]
        if len(chunk) > 0:
            chunks.append(chunk)

    print(f"Transcribing {len(chunks)} chunk(s)...")

    # 4. Transcribe each chunk and join
    all_texts = []

    for idx, chunk in enumerate(chunks, start=1):
        try:
            # Prepare input for this chunk
            inputs = processor(
                chunk,
                sampling_rate=16000,
                return_tensors="pt"
            )

            input_features = inputs.input_features.to(DEVICE)

            # Generate transcription for this chunk
            with torch.no_grad():
                predicted_ids = model.generate(input_features)

            text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            text = text.strip()

            print(f"Chunk {idx}/{len(chunks)}: {len(chunk)} samples -> '{text[:50]}...'")
            if text:
                all_texts.append(text)
        except Exception as e:
            print(f"Error transcribing chunk {idx}: {e}")

    # 5. Combine texts from all chunks
    full_text = " ".join(all_texts)
    return full_text.strip()


# ====== Routes ======
@app.route("/")
def home():
    """Show the main page with the form + list of notes from the DB."""
    conn = get_connection()
    rows = conn.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("index.html", notes=rows)


@app.route("/create", methods=["POST"])
def create_note():
    """Create a new note in the database (manual text)."""
    content = request.form.get("content", "").strip()

    if content:
        conn = get_connection()
        conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()

    return redirect(url_for("home"))


@app.route("/transcribe", methods=["POST"])
def transcribe_audio_route():
    """Handle audio file upload, transcribe it, and save as a note."""
    file = request.files.get("audio")

    if not file or file.filename == "":
        # No file selected
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        # Invalid extension
        print("Rejected file with invalid extension:", file.filename)
        return redirect(url_for("home"))

    # Save the file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        # Transcribe audio
        text = transcribe_audio(filepath)

        # Save transcription as a new note
        if text:
            conn = get_connection()
            conn.execute("INSERT INTO notes (content) VALUES (?)", (text,))
            conn.commit()
            conn.close()
    except Exception as e:
        print("Error during transcription:", e)
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

    return redirect(url_for("home"))


@app.route("/note/<int:note_id>")
def view_note(note_id):
    """View a single transcription with edit/download options."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, content, created_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    conn.close()

    if row is None:
        abort(404)

    return render_template("note.html", note=row)


@app.route("/note/<int:note_id>/edit", methods=["POST"])
def edit_note(note_id):
    """Update the content of a note."""
    new_content = request.form.get("content", "").strip()

    if new_content:
        conn = get_connection()
        conn.execute(
            "UPDATE notes SET content = ? WHERE id = ?",
            (new_content, note_id),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("view_note", note_id=note_id))


@app.route("/note/<int:note_id>/download")
def download_note(note_id):
    """Download a note as a .txt file."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, content FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    conn.close()

    if row is None:
        abort(404)

    content = row["content"]
    filename = f"transcription_{note_id}.txt"

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    """Delete a note from the database by id."""
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=8000)
