import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FILE = Path(__file__).parent.parent.parent / "app.log"

_configured = False


def setup_logging():
    global _configured
    if _configured:
        return
    _configured = True

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    file = RotatingFileHandler(
        _LOG_FILE, maxBytes=10_000_000, backupCount=5
    )
    file.setLevel(logging.INFO)
    file.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()  # IMPORTANT: avoid duplicate handlers
    root.addHandler(console)
    root.addHandler(file)


    # third-party noise control
    # firecrwl
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # cerebras
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
