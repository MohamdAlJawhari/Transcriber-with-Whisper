import os
import sys
import threading
import time
import urllib.request
import webbrowser

from waitress import serve

# PyInstaller --noconsole sets sys.stdout/sys.stderr to None; Transformers expects isatty().
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from transcriber import create_app


def _open_browser_when_ready(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                break
        except Exception:
            time.sleep(0.5)
    webbrowser.open(url)


def main() -> None:
    app = create_app()
    url = "http://127.0.0.1:8000"
    threading.Thread(
        target=_open_browser_when_ready,
        args=(url,),
        daemon=True,
    ).start()
    serve(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
