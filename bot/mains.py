import os
import time
import sys
#import logging
import asyncio
#logger = logging.getLogger(__name__)
from pyrogram.types import User
from os import execl
from sys import executable
from time import sleep, time

from pyrogram import Client, enums, filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram import filters, idle, Client
from pyrogram.filters import command, private, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters, idle
from bot.config import TG_CONFIG
from bot.config import token_file, client_secrets_json
from bot.helpers.utils import find_auth_code
from bot.config import gauth
from bot.config import START_MSG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pydrive2 import auth
from bot.services.tplay.api import TPLAY_API
from bot.helpers.utils import post_to_telegraph
import datetime
import logging
from pyrogram import Client
import pyromod
from pyromod import listen

logger = logging.getLogger(__name__)

loop = asyncio.get_event_loop()


LOGGER = logging.getLogger(__name__)



import nest_asyncio


nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


app = Client(
    name=TG_CONFIG.session_name,
    api_id=TG_CONFIG.api_id,
    api_hash=TG_CONFIG.api_hash,
    bot_token=TG_CONFIG.bot_token,
    
)

if TG_CONFIG.stringhi:
    USERBOT = Client(
        "cmuserbot",
        session_string=TG_CONFIG.stringhi,
        api_id=TG_CONFIG.api_id,
        api_hash=TG_CONFIG.api_hash,
    )
else:
    USERBOT = None

Start_Time = time.time()



@app.on_message(filters.chat(TG_CONFIG.sudo_users) & filters.command('gdrive'))
async def gdrive_helper(_, message):
    if len(message.text.split()) == 1:
        if not os.path.exists(client_secrets_json):
            await message.reply(
                "<b>No Client Secrets JSON File Found!</b>",
            )
            return
        
        if not os.path.exists(token_file):
            try:
                authurl = gauth.GetAuthUrl().replace("online", "offline")
            except auth.AuthenticationError:
                await message.reply(
                    '<b>Wrong Credentials!</b>',
                )
                return
            
            text = (
                '<b>Login In To Google Drive</b>\n<b>Send</b>`/gdrive [verification_code]`'
            )
            await message.reply(text, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔗 Log In URL", url=f"{authurl}")
                    ]
                ]
            ))
            return
        await message.reply(
            "<b>You're already logged in!\nTo logout type</b><code>/gdrive logout</code>",
        )
    #/gdrive logout
    elif len(message.text.split()) == 2 and message.text.split()[1] == 'logout':
        os.remove(token_file)
        await message.reply(
            '<b>You have logged out of your account!</b>',
        )
    #/gdrive [verification_code]
    elif len(message.text.split()) == 2:
        gauth.LoadCredentialsFile(token_file)
        try:
            if "localhost" in message.text.split()[1]:
                gauth.Auth(find_auth_code(message.text.split()[1]))
            else:
                gauth.Auth(message.text.split()[1])

        except auth.AuthenticationError:
            await message.reply('<b>Your Authentication code is Wrong!</b>')
            return
        gauth.SaveCredentialsFile(token_file)
        await message.reply(
            '<b>Authentication successful!</b>',
        )
    else:
        await message.reply('<b>Invaild args!</b>\nCheck <code>/gdrive</code> for usage guide')

@app.on_message(filters.chat(TG_CONFIG.sudo_users) & filters.incoming & filters.command(['webdl']) & filters.text)
def webdl_cmd_handler(app, message):
    if len(message.text.split(" ")) <= 2:
        message.reply_text(
            "<b>Syntax: </b>`/webdl -c [CHANNEL SLUG] [OTHER ARGUMENTS]`")
        return
    
    command = message.text.replace("/webdl", "").strip()
    if "-c" in command:
        from bot.services.tplay.main import TPLAY
        downloader = TPLAY(command, app, message)
        downloader.start_process()

            
@app.on_message(filters.command("trestart") & filters.private)
def restart_command(client, message):
    # Check if the message is from the owner
    if message.from_user.id == TG_CONFIG.owner_id:
        # Send a confirmation message to the owner
        message.reply("Restarting bot...")
        # Restart the bot
        os.execl(sys.executable, sys.executable, "-m", "bot")
    else:
        message.reply("You're not authorized to restart the bot!")

@app.on_message(filters.incoming & filters.command(['start']) & filters.text)
async def start_cmd_handler(app, message):
    code = "Access Denied" if message.from_user.id not in TG_CONFIG.sudo_users else "Welcome Admin"
    await message.reply_text(START_MSG.format(message.from_user.username, code))



def booted(bot):
    chats = TG_CONFIG.sudo_users

    try:
        logger.info(f"Added Counting")
    except Exception as e:
        logger.info(f"Main Error: {e}")

    for i in chats:
        try:
            bot.send_message(i, "The Bot is Restarted Now")
        except Exception:
            logger.info(f"Not found id {i}")


def start_bots():
    print("Processing.....")
    try:
        app.start()
        logger.info(f"Bot is Running....")
    except Exception as e:
        logger.info(f"Bot Error: {e}")

    if TG_CONFIG.stringhi:
        try:
            USERBOT.start()
            logger.info(f"UserBot is Running...")
        except Exception as e:
            logger.info(f"UserBot Error: {e}")

    booted(app)
    idle()

if __name__ == "__main__":
    try:
        loop.run_until_complete(start_bots())
    except KeyboardInterrupt:
        logger.info(f"Bots Stopped!! Problem in runloop")
