import logging
import sys

def setup_logging():
    logging_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=logging_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("helpdesk")
setup_logging()
