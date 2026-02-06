import os
import sys
import threading
import time
import urllib.request
import webbrowser

from waitress import serve


def _resolve_log_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.getcwd()
    return os.path.join(base_dir, "app.log")


# PyInstaller --noconsole sets sys.stdout/sys.stderr to None; Transformers expects isatty().
if sys.stdout is None or sys.stderr is None:
    log_file = open(_resolve_log_path(), "a", buffering=1, encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file

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


def _shutdown_when_idle(state: dict, idle_seconds: int) -> None:
    while True:
        time.sleep(5)
        if not state.get("had_activity"):
            continue
        if time.time() - state.get("ts", 0) > idle_seconds:
            os._exit(0)


def main() -> None:
    app = create_app()
    last_activity = {"ts": time.time(), "had_activity": False}

    @app.before_request
    def _touch_activity():
        last_activity["ts"] = time.time()
        last_activity["had_activity"] = True

    idle_timeout = int(app.config.get("IDLE_SHUTDOWN_SECONDS", 120) or 0)
    if idle_timeout > 0:
        threading.Thread(
            target=_shutdown_when_idle,
            args=(last_activity, idle_timeout),
            daemon=True,
        ).start()

    url = "http://127.0.0.1:8000"
    threading.Thread(
        target=_open_browser_when_ready,
        args=(url,),
        daemon=True,
    ).start()
    serve(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
