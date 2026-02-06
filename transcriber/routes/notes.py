import json
import os
import uuid
from flask import (
    Blueprint,
    Response,
    abort,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
    send_from_directory,
    stream_with_context,
)
from werkzeug.utils import secure_filename

from ..db import get_connection
from ..transcription import transcribe_audio, transcribe_audio_iter
from ..utils import allowed_file

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    """Show the main page with the form + list of notes from the DB."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, content, audio_path, created_at FROM notes ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("pages/index.html", notes=rows)


@bp.route("/ping", methods=["POST"])
def heartbeat():
    return ("", 204)


@bp.route("/create", methods=["POST"])
def create_note():
    """Create a new note in the database (manual text)."""
    content = request.form.get("content", "").strip()

    if content:
        conn = get_connection()
        conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()

    return redirect(url_for(".home"))


@bp.route("/transcribe", methods=["POST"])
def transcribe_audio_route():
    """Handle audio file upload, transcribe it, and save as a note."""
    file = request.files.get("audio")
    stream = request.headers.get("X-Transcribe-Stream") == "1"

    if not file or file.filename == "":
        if stream:
            return ("Missing audio file.", 400)
        return redirect(url_for(".home"))

    if not allowed_file(file.filename):
        print("Rejected file with invalid extension:", file.filename)
        if stream:
            return ("Invalid audio file type.", 400)
        return redirect(url_for(".home"))

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(filepath)
    try:
        print(f"Saved upload: {filepath} ({os.path.getsize(filepath)} bytes)")
    except Exception:
        print(f"Saved upload: {filepath} (size unavailable)")

    if stream:
        def generate():
            all_texts = []
            try:
                for idx, total, text in transcribe_audio_iter(filepath):
                    if text:
                        all_texts.append(text)
                    payload = {"type": "progress", "chunk": idx, "total": total}
                    yield json.dumps(payload) + "\n"

                full_text = " ".join(all_texts).strip()
                saved = False
                if full_text:
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO notes (content, audio_path) VALUES (?, ?)",
                        (full_text, unique_name),
                    )
                    conn.commit()
                    conn.close()
                    saved = True
                else:
                    if os.path.exists(filepath):
                        os.remove(filepath)

                payload = {"type": "done", "saved": saved}
                if not saved:
                    payload["message"] = "No transcription text was produced."
                yield json.dumps(payload) + "\n"
            except Exception as e:
                print("Error during transcription:", e)
                if os.path.exists(filepath):
                    os.remove(filepath)
                payload = {"type": "error", "message": "Error during transcription."}
                yield json.dumps(payload) + "\n"

        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        return Response(
            stream_with_context(generate()),
            mimetype="application/x-ndjson",
            headers=headers,
        )

    try:
        text = transcribe_audio(filepath)

        if text:
            conn = get_connection()
            conn.execute(
                "INSERT INTO notes (content, audio_path) VALUES (?, ?)",
                (text, unique_name),
            )
            conn.commit()
            conn.close()
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        print("Error during transcription:", e)
        if os.path.exists(filepath):
            os.remove(filepath)

    return redirect(url_for(".home"))


@bp.route("/note/<int:note_id>")
def view_note(note_id):
    """View a single transcription with edit/download options."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, content, audio_path, created_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    conn.close()

    if row is None:
        abort(404)

    return render_template("pages/note.html", note=row)


@bp.route("/note/<int:note_id>/edit", methods=["POST"])
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

    return redirect(url_for(".view_note", note_id=note_id))


@bp.route("/note/<int:note_id>/download")
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


@bp.route("/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    """Delete a note from the database by id."""
    conn = get_connection()
    row = conn.execute(
        "SELECT audio_path FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    if row and row["audio_path"]:
        audio_file = os.path.join(current_app.config["UPLOAD_FOLDER"], row["audio_path"])
        if os.path.exists(audio_file):
            os.remove(audio_file)

    return redirect(url_for(".home"))


@bp.route("/audio/<path:filename>")
def audio_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
