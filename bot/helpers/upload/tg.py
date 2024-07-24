import os
import time
from bot.helpers.utils import humanbytes, get_duration, get_thumbnail, progress_for_pyrogram

from main import BOT as appl

class tgUploader:
    def __init__(self, appl, msg):
        self.app = appl
        self.msg = msg

    def upload_file(self, file_path):
        try:

            file_name = os.path.basename(file_path)  
            duration = get_duration(file_name)
            thumb = get_thumbnail(file_name, "", duration / 2)

            file_size = humanbytes(os.stat(file_path).st_size)

            caption = '''<code>{}</code>'''.format(file_name)

            progress_args_text = "<code>[+]</code> <b>{}</b>\n<code>{}</code>".format("Uploading", file_name)

            self.appl.send_video(
                video=file_path, 
                chat_id=self.msg.chat.id, 
                caption=caption, 
                progress=progress_for_pyrogram, 
                progress_args=(
                        progress_args_text,
                        self.msg, 
                        time.time()
                ), thumb=thumb, duration=duration, width=1280, height=720
            )
            os.remove(file_path)
            os.remove(thumb)
            self.msg.delete()
        except Exception as e:
            print(e)
            self.msg.edit(f"`{e}`")
