from bot.__init__ import create_client
from bot.config import TG_CONFIG
import pyrogram
from pyrogram import Client as client


import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger("pyrogram").setLevel(logging.WARNING)

from bot import create_client

client = create_client(TG_CONFIG.stringhi)
if client:
    IS_PREMIUM_USER = client.me.is_premium
    logging.info("Bot started successfully")
    # Use the client object here
    print("Client object:", client)
else:
    logging.error("Failed to create client")
