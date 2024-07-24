import logging
import time
import nest_asyncio
from pyrogram import Client
import pyromod
from bot.config import TG_CONFIG as Config
from pyromod import listen
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


BOT = Client(
    name=Config.session_name,
    api_id=Config.api_id,
    api_hash=Config.api_hash,
    bot_token=Config.bot_token,
    plugins=dict(root="bot"),
)

if Config.stringhi:
    USERBOT = Client(
        "cmuserbot",
        session_string=Config.stringhi,
        api_id=Config.api_id,
        api_hash=Config.api_hash,
    )
else:
    USERBOT = None

Start_Time = time.time()
