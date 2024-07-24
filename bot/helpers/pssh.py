import re
import base64
import subprocess
import requests
from bot.config import ytdlp
from bot.config import PROXY_CONFIG, proxies

def extract_pssh(text):
    try:
        pattern = rb"<cenc:pssh>(.*?)</cenc:pssh>"
        matches = re.findall(pattern, text)
        if matches:
            smaller_pssh = min(matches, key=len)
            return smaller_pssh.strip().decode()
        else:
            return None
    except Exception as e:
        print("Error:", e)
        return None


def extract_pssh_ytdlp(url):

    cmd = [ytdlp]

    if PROXY_CONFIG.proxy_url and PROXY_CONFIG.proxy_url.strip() and PROXY_CONFIG.USE_PROXY_WHILE_DOWNLOADING:  # Check if PROXY_CONFIG.proxy_url is not empty or None
        cmd.extend(["--proxy", PROXY_CONFIG.proxy_url])

    cmd.extend([
        "--geo-bypass-country",
        "IN",
        "--allow-unplayable-formats",
        "--skip-download",
        "--dump-pages",
        url
    ])

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Capture the output as text
            check=True  # Raise an exception if the command fails
        )

        return extract_pssh(base64.b64decode(result.stdout.split("\n")[3]))

    except subprocess.CalledProcessError as e:
        print(e)
        return None

def get_mpd_text(url):
    cmd = [ytdlp]

    if PROXY_CONFIG.proxy_url and PROXY_CONFIG.proxy_url.strip() and PROXY_CONFIG.USE_PROXY_WHILE_DOWNLOADING:  # Check if PROXY_CONFIG.proxy_url is not empty or None
        cmd.extend(["--proxy", PROXY_CONFIG.proxy_url])

    cmd.extend([
        "--geo-bypass-country",
        "IN",
        "--allow-unplayable-formats",
        "--skip-download",
        "--dump-pages",
    ])

    cmd.extend([url])

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Capture the output as text
            check=True  # Raise an exception if the command fails
        )

        return base64.b64decode(result.stdout.split("\n")[3]).decode("utf-8")

    except subprocess.CalledProcessError as e:
        print(e)
        return None
    

def get_pssh(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "x-playback-session-id" : "9c7631d21edd4a65a92b2b641c8a13a2-1634808345996"
            }, proxies=proxies
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
    

def extract_default_kid(mpd):
    xml_data = requests.get(mpd, proxies = proxies).text
    pattern = r'cenc:default_KID="([^"]+)"'
    match = re.search(pattern, xml_data)
    if match:
        return match.group(1).strip()
    else:
        raise Exception("Enable to find KID")