import logging


def get_logger() -> logging.Logger:
    # Create a logger object
    logger = logging.getLogger("cs_deals_logger")
    logger.setLevel(logging.DEBUG)  # Set the base level for all logs

    # Create a file handler for the log file
    log_file_name = "deals_log.log"
    file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log everything from DEBUG level up

    # Define a simple log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Attach the file handler to the logger
    if not logger.handlers:  # Avoid adding handlers multiple times in case of imports
        logger.addHandler(file_handler)

    return logger
