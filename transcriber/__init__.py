from flask import Flask

from .config import BASE_DIR, Config
from .db import init_db
from .routes import notes_bp
from .transcription import preload_model
from .utils import ensure_directory


def create_app(config_object=Config):
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(config_object)

    ensure_directory(app.config["UPLOAD_FOLDER"])
    init_db(app)

    app.register_blueprint(notes_bp)

    if app.config.get("PRELOAD_MODEL"):
        preload_model(app)

    return app
