import os
from pydrive2.auth import GoogleAuth
from bot.helpers.cookies import get_cookies

currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)


class TG_CONFIG:
    api_id = 4857766
    premium = False
    session_name = "bhootkiduniya"  # Replace with your desired session name

  #  session_string = ""  # Replace with your Telegram session string (optional)

    log_file = "log.txt"  # 
    api_hash = "6c3c6facf5598a4b318e138f8c407028"
    stringhi = "BQD6zg0As0jMe838fXnvcfpUgY_05uuCaDpsOnMDqd9lBe1A02aKjZPzpqzKH_u1N-53bSPJEG0t2amKfsuYIoFTaidHXSy8BKiE2VTZ-dbJ8RyU-FlV1UUo6H8D3OmOXOVRJPdB09-Og99nqklo-9ZhCt9fPNc033qT3wUjA7YZXF5AlYX6E3AbXz216tcWgKqPxOdVJ2J3lsmkjq810pcZKS4HBJFc5uAIpCZf2Gfh2Eh9ohbkPo4YuDy9uKBaf3yoK3_nxb_a7aSPzfvq1fDvYO3YmzavdWjd9dyYLIV_8ZLv0O-p6rOMbj-nySM7GqQBUsp095QeqFopkKs_z283Hl8T-AAAAABHP54rAA"
    UPSTREAM_REPO = "https://github.com/aryanchy4499/mtl1"
    UPSTREAM_BRANCH = "main"
    bot_token = "7301903414:AAEXa7-mPWmokaOGWK0gNmdpXZlUrzEfJ_A"
    owner_id = 1996570767
    #DEVS or #OWNERS
    sudo_users = [1596559467, -1002230874428, -1002233833025, 1996570767]
    session = "maheshiassistantbot"
    max_file_size = 200000000  # 2GB
    video_width = 1280
    video_height = 720
    bot_creater = "IDK"  # Don't Remove if you Respect the DEV

    bot_creater_id = "@OFFICIALCREATER"  # Don't Remove if you Respect the DEV


class UPLOAD_CONGIF:
    upload_to = "tg" #tg, ftp, gdrive
    default_upload_to = "tg"


class ScaryGhost(object):

    owner = "1996570767"

    log_channel = "-1001946386363"


class GDRIVE_CONFIG:
    #for Gdrive (Leave it as Empty String if not Gdrive Upload is turned ON)
    root_folder_id = ""

    #keep it empty if you don't have index link or don't touch
    indexlink_format = "https://example.workers.dev/0:/{}/{}"

    is_making_drive_files_public = True


class GD_SHARER_CONFIG:

    is_uploading_to_filepress = False

    #Don't add a trailing slash at the end (keep in this format only - https://new5.filepress.store)
    filepress_url = "https://new9.filepress.store"
    
    cookie_path = dirPath + "/cookies/filepress.txt"
    _, dict_cookies = get_cookies(cookie_path)
    
    filepress_connect_sid_cookie_value = dict_cookies.get("connect.sid")


class PROXY_CONFIG:
    #Keep it as a empty string if you don't have proxy
    proxy_url = ""
    USE_PROXY_WHILE_DOWNLOADING = False


class FTP_CONFIG:
    #FTP Creds
    ftp_url = ""

    ftp_domain = ""
    
    ftp_user = ""
    
    ftp_password = ""


class FILENAME_CONFIG:

    filename_format = "p2p"  # p2p or non-p2p

    p2p_audio_bitrate = "K"

    non_p2p_audio_bitrate = "Kbps"

    underscore_before_after_group_tag = "__"

    language_order = ['hi', 'ta', 'te', 'bn', 'gu', 'pa', 'as', 'or',
                    'ml', 'mr', 'kn', 'th', 'ja', 'th', 'id', 'ms', 'ko', 'bho', 'bh', 'en']

    default_group_tag = "Team Auspicious" # Don't change it if you Respect the DEV

    #Dict made to add Group Tag according to the user requesting to DL (according to there TG ID) if not in list then takes the default_group_tag
    group_tag_mapping = {
        '7172796863': 'Team Auspicious',
        '1596559467' : 'Team Auspicious'
    }


DL_DONE_MSG = """
✅ <b> Task Completed In </b> <code>{}</code>

<b>FileName : </b> <code>{}</code>
<b>OTT : </b> <code>{}</code>
<b>Size : </b> <code>{}</code>
"""


START_MSG = """
<b>Hello <code>@{}</code>,
A TG WEB-DL Bot</b>

> <code>{}</code>

<b>Made by @maheshsirop</b>
"""

SIMPLE_CAPTION = '''<code>{}</code>'''

LOG_MESSAGE = "<code>[+]</code> <b>{}</b>\n<b><code>[+]</code> <b>{} : </b><code>{}</code>"


proxies = {
    "https": PROXY_CONFIG.proxy_url,
    "http": PROXY_CONFIG.proxy_url
} if PROXY_CONFIG.proxy_url and PROXY_CONFIG.proxy_url.strip() else None

tplay_path = os.path.join(
    dirPath, "static", "tplay.json")

languages_info_file_path = os.path.join(
    dirPath, "static", "languages_info.json")

client_secrets_json = os.path.join(dirPath, "static", "client_secrets.json")

token_file = os.path.join(dirPath, "static", "session")

dl_folder = os.path.join(dirPath, "downloads")  

os.makedirs(dl_folder) if not os.path.exists(dl_folder) else None

iswin = 1 if os.name == "nt" else 0


if iswin == 0:
    aria2c = dirPath + "/binaries/aria2c"
    mp4decrypt = dirPath + "/binaries/mp4decrypt"
    ytdlp = dirPath + "/binaries/yt-dlp"

    os.system(f"chmod 777 {aria2c} {mp4decrypt} {ytdlp}")
else:
    aria2c = dirPath + "/binaries/aria2c.exe"
    mp4decrypt = dirPath + "/binaries/mp4decrypt.exe"
    ytdlp = dirPath + "/binaries/yt-dlp.exe"


gauth = GoogleAuth()
GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = client_secrets_json
