import os
from flask import current_app

# Ensure the specified directory exists
def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# Check if the uploaded file has an allowed extension
def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]
