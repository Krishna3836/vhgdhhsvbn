import os
import logging
from pyrogram import Client, enums
from bot.config import TG_CONFIG
LOG_FILE = 'log.txt'
USER_SESSION_STRING_KEY = 'tringhi'

# Set up logging
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Set logging level for pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)


