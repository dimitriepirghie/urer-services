import logging
import sys

logs_format = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s")
logger = logging.getLogger('URER Logger')
logger.setLevel(logging.DEBUG)
channel = logging.StreamHandler(sys.stdout)

channel.setFormatter(logs_format)
logger.addHandler(channel)