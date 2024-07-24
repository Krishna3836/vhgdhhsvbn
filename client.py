import asyncio
import logging
import pyromod
from pyrogram import idle
from pyromod import listen
from bot.config import TG_CONFIG as Config
from main import BOT, USERBOT

logger = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


async def booted(bot):
    chats = TG_CONFIG.sudo_users

    try:
        logger.info(f"Added Counting")
    except Exception as e:
        logger.info(f"Main Error: {e}")

    for i in chats:
        try:
            await bot.send_message(i, "The Bot is Restarted 鈾伙笍 Now")
        except Exception:
            logger.info(f"Not found id {i}")


async def start_bots():
    print("Processing.....")
    '''   
    try:
        await BOT.start()
        logger.info(f"Bot is Running....")
    except Exception as e:
        logger.info(f"Bot Error: {e}")
    '''

    await BOT.start()   
    if TG_CONFIG.stringhi:
        try:
            await USERBOT.start()
            logger.info(f"UserBot is Running...")
        except Exception as e:
            logger.info(f"UserBot Error: {e}")

    await booted(BOT)
    await idle()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start_bots())
    except KeyboardInterrupt:
        logger.info(f"Bots Stopped!! Problem in runloop")
