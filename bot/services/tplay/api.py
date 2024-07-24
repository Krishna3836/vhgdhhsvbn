import re
import json
import requests
from bot.config import tplay_path
from bot.helpers.utils import timestamp_to_datetime
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import random

API_ALL_CHANNELS = "https://kong-tatasky.videoready.tv/content-detail/pub/api/v1/channels?limit=1000"
FETCHER = "https://tplayapi.code-crafters.app/321codecrafters/fetcher.json"
HMAC = "https://tplayapi.code-crafters.app/321codecrafters/hmac.json?random={}"
HMAC_v2 = "https://yuvraj43.xyz/test/ghjqw/manifest.mpd?id=587"

class TPLAY_API:
    def __init__(self, channel_slug: str):
        self.channel_slug = channel_slug
        self.channels = self._fetch_channels()

    def _fetch_channels(self) -> dict:
        response = requests.get(FETCHER)
        response.raise_for_status()
        return response.json()

    def get_hmac_v2(self) -> str:
        response = requests.get(HMAC.format(random.randint(10, 99)))
        response.raise_for_status()
        return response.json()['data']['hmac']['hdnea']['value']

    def get_hmac(self) -> str:
        response = requests.get(HMAC.format(random.randint(10, 99)))
        response.raise_for_status()
        data = response.json()
        hdnea = data['data']['hmac']['hdnea']['value']
        return hdnea.split('exp=', 1)[1]

    def get_data(self) -> dict:
        for channel in self.channels['data']['channels']:
            if channel.get('name').replace(" ", "").lower() == self.channel_slug.lower():
                return channel
        return {}

    def get_channel_id(self) -> int:
        response = requests.get(API_ALL_CHANNELS)
        response.raise_for_status()
        all_channels = response.json()['data']['list']
        for channel in all_channels:
            if channel.get('title').replace("!", "").replace("Hindi", "").replace(" ", "") == self.channel_slug:
                return channel.get('id')
        return 0

def within_12_hours(timestamp: str) -> bool:
    """
    Check if the provided timestamp is within the last 12 hours.
    """
    provided_time = parser.isoparse(timestamp)
    provided_time = provided_time.astimezone(pytz.timezone('Asia/Kolkata'))
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    time_difference = current_time - provided_time
    return time_difference < timedelta(hours=12)
