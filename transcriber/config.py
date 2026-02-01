from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    DB_PATH = str(BASE_DIR / "notes.db")
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a", "webm"}
    MODEL_DIR = str(BASE_DIR / "model")
    MAX_CHUNK_SECONDS = 25
    PRELOAD_MODEL = True
