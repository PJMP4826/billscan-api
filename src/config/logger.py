import logging
import os
import colorlog
from pathlib import Path

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Consola (siempre activa, estándar en contenedores y serverless)
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s | %(filename)s:%(lineno)d | %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Archivo (activado explícitamente por configuración, ej. el .env local)
    if os.getenv("LOG_TO_FILE", "false").lower() == "true":
        BASE_DIR = Path(__file__).resolve().parents[2]
        LOG_DIR = BASE_DIR / "logs"
        LOG_DIR.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            filename=LOG_DIR / "app.log",
            mode="a",
            encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)