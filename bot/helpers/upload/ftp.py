import os
import time
from bot.helpers.utils import get_readable_time, humanbytes
from bot.config import DL_DONE_MSG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import FTP_CONFIG
from ftplib import FTP
from urllib.parse import quote


class ftpUploader:
    def __init__(self, app, msg, process_before_upload_start_time):
        self.c_time = process_before_upload_start_time
        self.app = app
        self.msg = msg
        self.ftp = FTP(FTP_CONFIG.ftp_url)
        try:
            self.ftp.login(user=FTP_CONFIG.ftp_user, passwd=FTP_CONFIG.ftp_password)
        except Exception as e:
            self.msg.edit(f"`Unable To Login - {e}`")
            raise Exception(e)

    def create_subfolder(self, folder_path):
        folders = folder_path.split("/")
      
        for i in range(1, len(folders) + 1):
            partial_path = "/".join(folders[:i])
            try:
                self.ftp.mkd(partial_path)
                print(f"Created directory: {partial_path}")
            except Exception as e:
                if "550 Directory already exists" not in str(e):
                    print(f"Warning: Error creating directory {partial_path}: {e}")

    def upload_file(self, file_path, subfolder_path, ott="OTT"):
        try:
            self.create_subfolder(subfolder_path)
            file_name = os.path.basename(file_path)  

            remote_file_path =  f"{subfolder_path}/{file_name}"
            
            with open(file_path, "rb") as file:
                self.ftp.storbinary(f"STOR {remote_file_path}", file)

            self.ftp.quit()

            result_path = "{}/{}/{}".format(FTP_CONFIG.ftp_domain, quote(subfolder_path), quote(file_name))

            inline_keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🔗 LINK", url=result_path),
                        ]
                    ]
                )
            caption = DL_DONE_MSG.format(
                get_readable_time(time.time() - self.c_time),
                os.path.basename(file_path),
                ott,
                humanbytes(os.stat(file_path).st_size)
            )

            self.msg.edit(
            text=caption,
            reply_markup=inline_keyboard
        )
            os.remove(file_path)
        except Exception as e:
            print(e)
            self.msg.edit(f"`{e}`")