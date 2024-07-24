import os
import re
import json
import requests
import pytz
import ffmpeg, time, math
from urllib.parse import urlparse
from bot.config import languages_info_file_path
from bot.config import FILENAME_CONFIG
from bot.config import GD_SHARER_CONFIG
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from datetime import datetime, timedelta
from telegraph import Telegraph


colored_text_config = False

MESSAGE = "\n[+] {}\n[+] {} : {}"

def print_message(first, second, third):
    print(MESSAGE.format(colored_text(first, "green"), colored_text(
        second, "blue"), colored_text(third, "cyan")))


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "\n[{0}{1}] \n**Process**: `{2}%`\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "`{0} of {1}`\n**Speed:** `{2}/s`\n**ETA:** `{3}`\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass

def colored_text(text, color):
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m",
    }
    if colored_text_config is True:
        return f"{colors[color]}{text}{colors['reset']}"
    else:
        return text
    
def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
        return metadata.get('duration').seconds
    else:
        return 0


def get_thumbnail(in_filename, path, ttl):
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
        return None


def find_auth_code(url):
    pattern = r'code=([^&]+)'
    match = re.search(pattern, url)

    if match:
        code_value = match.group(1)
        return code_value
    return None


def custom_sort(audio):
    # Assign a high index if the language is not in language_order
    lang_index = FILENAME_CONFIG.language_order.index(
        audio["lang"]) if audio["lang"] in FILENAME_CONFIG.language_order else len(FILENAME_CONFIG.language_order)
    return (lang_index, audio["lang"])


def language_mapping(language_code, return_key=None):

    with open(languages_info_file_path, "r") as json_file:
        language_info = json.load(json_file)

    for code, info in language_info.items():
        if (
            code == language_code
            or info.get("639-1") == language_code
            or info.get("639-2") == language_code
            or "en" in info and info["en"][0].lower() == language_code.lower()
        ):
            return_value = info.get(return_key)
            if return_key == "en" and return_value:
                return return_value[0]
            return return_value or info.get("639-1")

    raise Exception(f"Language code '{language_code}' not found.")


def get_pssh(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            },
        )
        text = response.text
        # print(text)
        pattern = r"<cenc:pssh>(.*?)</cenc:pssh>"
        matches = re.findall(pattern, text)
        if matches:
            smaller_pssh = min(matches, key=len)
            return smaller_pssh.strip()
        else:
            return None
    except requests.exceptions.RequestException as e:
        print("Error occurred while making the request:", e)
        return None


def get_zee5_id(url):
    id_pattern = r'/details/[^/]+/([^/]+)/?$'
    match = re.search(id_pattern, url)
    if match:
        return match.group(1).split("?")[0]
    else:
        return None


def get_unext_id(url):
    pattern = r'(SID\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None


def read_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content.strip()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def find_mx_url_lang(url):
    slug = url.replace("https://www.mxplayer.in",
                       "").replace("https://mxplayer.in", "")
    res = requests.get("https://seo.mxplay.com/v1/api/seo/get-url-details?url={}&device-density=2&userid=e5951dac-4e23-4f84-9c66-14cb22e774e5&platform=com.mxplay.desktop&content-languages=hi,en&kids-mode-enabled=false".format(slug)).json()
    meta_desc = res['data']['description']

    small_lang_map = {
        "Hindi": "hin",
        "Tamil": "tam",
        "Telugu": "tel",
        "Kannada": "kan",
        "Malayalam": "mal",
        "Bhojpuri": "bho"
    }

    langs = ["Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bhojpuri"]
    for big_lang, small_lang in small_lang_map.items():
        if big_lang in meta_desc:
            return small_lang_map.get(big_lang, "hin")
    return "hin"


def parse_file_name(init_file_name, video_resolution, GR = "Conan76"):
    
    tv_show_pattern = r'(.+?)\s*S(\d+)E(\d+)'
    movie_pattern = r'(.+?)\s*(\d{4})$'
    unknown_pattern = r'(.+)'
    
    resolution = video_resolution

    tv_show_match = re.match(tv_show_pattern, init_file_name, re.IGNORECASE)
    movie_match = re.match(movie_pattern, init_file_name)
    unknown_match = re.match(unknown_pattern, init_file_name)

    if tv_show_match:
        show_title = tv_show_match.group(1).replace(".", " ").strip()
        season_number = int(tv_show_match.group(2))
        episode_number = int(tv_show_match.group(3))
        return {
            'type': 'TV Show',
            'show_title': show_title,
            'season_number': season_number,
            'episode_number': episode_number,
            'release_year': None,
            'path': "Series/{}/S{:02d}/{}".format(show_title, season_number, resolution)
        }
    elif movie_match:
        movie_name = movie_match.group(1).replace(".", " ").strip()
        release_year = int(movie_match.group(2))
        return {
            'type': 'Movie',
            'movie_name': movie_name,
            'release_year': release_year,
            'path': "Movie/{} - {}/{}".format(movie_name, release_year, resolution)
        }
    elif unknown_match:
        unknown_name = unknown_match.group(1).strip()
        return {
            'type': 'Movie - Unknown',
            'name': unknown_name,
            'release_year': 0000,
            'path': "Movie/{}".format(unknown_name)
        }
    else:
        return {
            'type': 'Unknown'
        }


def find_mini_tv_audio_track(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        regex = r'"audioTracks":\["(.*?)"\]'
        match = re.search(regex, html_content)

        if match and match.group(1):
            audio_track = match.group(1)
            return audio_track.lower()[:3]
        else:
            return None
    else:
        print("Failed to fetch URL content.")
        return None


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result


def get_group_tag(userID):
    userID = str(userID)
    return FILENAME_CONFIG.group_tag_mapping.get(userID, FILENAME_CONFIG.default_group_tag)


def get_file_ext(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    parts = path.split('/')
    filename = parts[-1]
    # Split the filename by '.' to get the extension
    filename_parts = filename.split('.')
    extension = filename_parts[-1]
    return extension


def extract_gdrive_id(driveLink):
    # Regular expression pattern to match file ID from Google Drive URLs
    pattern = r"(?<=/d/|id=)([\w-]+)(?=/|$)"

    match = re.search(pattern, driveLink)
    if match:
        return match.group(1)
    else:
        return None


def upload_to_filepress(driveLink):

    driveID = extract_gdrive_id(driveLink)

    try:
        cookies = {
            'connect.sid': GD_SHARER_CONFIG.filepress_connect_sid_cookie_value,
        }

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en,en-US;q=0.9,en-IN;q=0.8',
            'content-type': 'application/json',
            'origin': GD_SHARER_CONFIG.filepress_url,
            'referer': f'{GD_SHARER_CONFIG.filepress_url}/add-file',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }

        json_data = {
            'id': driveID,
            'addType': 'self',
            'isAutoUploadToStream': True,
        }

        response = requests.post('{}/api/file/add/'.format(GD_SHARER_CONFIG.filepress_url),
                                 cookies=cookies, headers=headers, json=json_data).json()
        return "{}/file/{}".format(GD_SHARER_CONFIG.filepress_url, response['data']['_id'])

    except Exception as e:
        print(e)
        return None
    
def getTplayTime(time1 , time2 , data):
    # begin = int(data) / 1000
    # naive = str(time.strftime('%Y%m%d', time.localtime(begin)))
    date , month , year = data.split("/")
    hh, mm, ss = map(int, time1.split(':'))
    hh2 , mm2 , ss2 = map(int, time2.split(':'))
    t1 = timedelta(hours=hh, minutes=mm , seconds=ss)
    t2 = timedelta(hours=hh2, minutes=mm2 , seconds=ss2)
    f = str(t1 - t2)
    
    # if len(f.split(":")[0]) == 1:
    #         g = str(year) + str(month) + str(int(date) - 1) + "T" + "0" + str(f.replace(":" , ""))
    # else:
    #         g = str(year) + str(month) + str(int(date) - 1) + "T" + str(f.replace(":" , ""))
    
    if "-1" in f:
        if len(f.split(":")[0]) == 1:
            date_sub = int(date) - 1
            if int(date_sub) < 10:
                
                g = str(year) + str(month) + "0" + str(date_sub) + "T" + "0" + str(f.replace(":" , ""))
            else:
                g = str(year) + str(month) + str(date_sub) + "T" + "0" + str(f.replace(":" , ""))
        else:
            date_sub = int(date) - 1
            if int(date_sub) < 10:

                g = str(year) + str(month) + "0" + str(date_sub) + "T" + str(f.replace(":" , ""))
            else:
                g = str(year) + str(month) + str(date_sub) + "T" + str(f.replace(":" , ""))
            
        return g.replace("-1 day, " , "")
        
    else:
        if len(f.split(":")[0]) == 1:
            g = str(year) + str(month) + str(date) + "T" + "0" + str(f.replace(":" , ""))
        else:
            g = str(year) + str(month) + str(date) + "T" + str(f.replace(":" , ""))
        return g

def get_tplay_past_details(date_text):
    sTime, eTime = date_text.split("-")
    begin = getTplayTime(sTime.split("+")[1] , "05:30:00" , sTime.split("+")[0])
    end = getTplayTime(eTime.split("+")[1] , "05:30:00" , eTime.split("+")[0])
    date_data = sTime.split("+")[0]
    date_data = datetime.strptime(date_data, "%d/%m/%Y").strftime("%d-%m-%Y")
    time_data = "[" + sTime.split('+')[1][:len(sTime.split('+')[1]) - 3] + "-" + eTime.split('+')[1][:len(eTime.split('+')[1]) - 3] + "]"+ ".[" + date_data + "]"

    return begin, end, date_data, time_data



def add_quotes_to_title(input_string):
    args_list = input_string.split()
    
    title_list = None
    
    #First Finds the index wherein title comes and then removes everything before that 
    for i, arg in enumerate(args_list):
        if arg == "-title" or arg == "--title":
            title_list = args_list[i + 1:]
            break

    #Additionally finds if there are other arguments in the list finds the index using - or -- in argument and then removes everything after that

    for i, arg in enumerate(title_list):
        if "-" in arg or "--" in arg:
            title_list = title_list[:i]
            break

    new_title =  "'" + ' '.join(title_list) + "'"
    new_input_string = input_string.replace(' '.join(title_list) , new_title)
    return new_input_string




def timestamp_to_datetime(timestamp, timezone = "Asia/Kolkata"):
    dt_object = datetime.fromtimestamp(timestamp / 1000, tz=pytz.utc)
    dt_object = dt_object.astimezone(pytz.timezone(timezone))  
    return dt_object.strftime("%d/%m/%Y+%H:%M:%S")



def post_to_telegraph(content):

    telegraph = Telegraph()
    telegraph.create_account(short_name='conan76')
    
    response = telegraph.create_page(
        'Schedule',
        html_content=content
    )

    return response['url']