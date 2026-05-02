import datetime
import logging
import os

CURRENT_DATETIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# os.makedirs("logs", exist_ok=True)


def init_logging(name: str) -> logging.Logger:
    """Initializes logging configuration.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s",
        handlers=[
            # logging.FileHandler(os.path.join("logs", f"app_{CURRENT_DATETIME}.log")),
            logging.StreamHandler(),
        ],
    )
    # Silence verbose internal libraries we don't need in normal logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(name)
    return logger
