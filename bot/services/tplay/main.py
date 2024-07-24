from bot.config import LOG_MESSAGE
from bot.helpers.parser.mpd import mpd_table
from bot.helpers.ott_parser import ott_argument_parser
from bot.services.tplay.api import TPLAY_API
from bot.helpers.utils import get_tplay_past_details
from bot.helpers.download.mpd import Processor
from bot.helpers.utils import add_quotes_to_title

class TPLAY:
    def __init__(self, command, app, message):
        self.app = app
        self.message = message
        self.ott = "TPLAY"

        if any(x in command for x in ["-title", "--title"]):
            command = add_quotes_to_title(command)

        try:
            self.parsed_args = ott_argument_parser(command, "tplay")
        except Exception as e:
            self.message.reply_text(f'''<code>{e}</code>''')
            return
        self.ott_api = TPLAY_API(self.parsed_args.channel)

    @staticmethod
    def check_catchup_data(parsed_args):
        missing_args = []
        if not parsed_args.channel:
            missing_args.append("channel")
        if not parsed_args.start:
            missing_args.append("start")
        if not parsed_args.end:
            missing_args.append("end")

        if missing_args:
            return False, f"Missing arguments: {', '.join(missing_args)}"
        else:
            return True, ""

    def start_process(self):
        msg = self.message.reply_text(LOG_MESSAGE.format("Processing...", "Channel ", self.parsed_args.channel))
        if not self.check_before_continue(msg):
            return

    def check_before_continue(self, msg):
        try:
            if self.parsed_args.channel:
                self.channel_data = self.ott_api.get_data()
        except Exception as e:
            msg.edit(LOG_MESSAGE.format("ERROR", "CHANNEL", e))
            return False

        if self.parsed_args.start:
            can_continue, msg_text = self.check_catchup_data(self.parsed_args)

            if not can_continue:
                msg.edit(LOG_MESSAGE.format("ERROR", "CATCHUP", msg_text))
                return False

        self.download_catchup(msg)
        return True

    def download_catchup(self, msg):
        date_text = "{}-{}".format(self.parsed_args.start, self.parsed_args.end)
        begin, end, date_data, time_data = get_tplay_past_details(date_text)
        hmac = self.ott_api.get_hmac()
        mpd = self.channel_data.get('manifest_url').replace("bpweb", "bpprod").replace(".akamaized", "catchup.akamaized") + "?begin=" + str(begin) + "&end=" + str(end) + "&" + hmac
        key = [keys for keys in self.channel_data.get('clearkeys') if keys.get('source') == "media_segment"][0]['hex']

        init_title = self.parsed_args.title if self.parsed_args.title != "" else self.channel_data.get('name')

        name = "{} {}".format(init_title, time_data)

        msg.edit(LOG_MESSAGE.format("Downloading...", "Catchup", name))
        self.msg.delete()
        Processor(
            self.app, 
            self.message, 
            mpd, 
            key, 
            video_resolution=self.parsed_args.resolution,
            video_quality=self.parsed_args.vquality, 
            audio_quality=self.parsed_args.aquality,
            alang=self.parsed_args.alang, 
            init_file_name=name, 
            ott=self.ott, 
            fallback_language=None,
            headers=self.channel_data.get('manifest_headers')).start_process()
