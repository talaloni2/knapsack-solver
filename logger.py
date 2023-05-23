import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# add handler to logger
logger.addHandler(ch)
