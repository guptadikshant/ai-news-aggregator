import datetime
import logging
import os

CURRENT_DATETIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

os.makedirs("logs", exist_ok=True)


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(os.path.join("logs", f"app_{CURRENT_DATETIME}.log")),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)
    return logger
