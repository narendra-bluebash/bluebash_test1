import logging
import colorlog

def setup_logger(logger_name: str, debug_color="white", info_color="green", propagate=False):
    color_handler = colorlog.StreamHandler()
    log_colors = {
        "DEBUG": debug_color,
        "INFO": info_color,
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
    color_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors=log_colors
        )
    )
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(color_handler)
    logger.propagate = propagate
    return logger
