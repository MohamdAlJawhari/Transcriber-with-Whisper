import os
from flask import Blueprint, Response, abort, redirect, render_template, request, url_for, current_app
from werkzeug.utils import secure_filename

from ..db import get_connection
from ..transcription import transcribe_audio
from ..utils import allowed_file

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    """Show the main page with the form + list of notes from the DB."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, content, created_at FROM notes ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("pages/index.html", notes=rows)


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

    if not file or file.filename == "":
        return redirect(url_for(".home"))

    if not allowed_file(file.filename):
        print("Rejected file with invalid extension:", file.filename)
        return redirect(url_for(".home"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        text = transcribe_audio(filepath)

        if text:
            conn = get_connection()
            conn.execute("INSERT INTO notes (content) VALUES (?)", (text,))
            conn.commit()
            conn.close()
    except Exception as e:
        print("Error during transcription:", e)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    return redirect(url_for(".home"))


@bp.route("/note/<int:note_id>")
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
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    return redirect(url_for(".home"))
