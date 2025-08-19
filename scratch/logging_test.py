import logging
from cocotb.logging import default_config

try:
    default_config()
except RuntimeError:
    pass
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("name")
logging.addLevelName(5, "TEST")
logger.setLevel(5)
logger.log(5, "Test msg")
