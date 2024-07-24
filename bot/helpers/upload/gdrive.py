import os
import time
from pydrive2.drive import GoogleDrive
from bot.helpers.utils import get_readable_time, humanbytes
from bot.config import gauth, client_secrets_json, token_file
from bot.config import client_secrets_json, token_file
from bot.config import DL_DONE_MSG, GDRIVE_CONFIG
from bot.config import GD_SHARER_CONFIG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote
from bot.helpers.utils import upload_to_filepress


class GoogleDriveUploader:
    def __init__(self, app, msg, process_before_upload_start_time):
        self.c_time = process_before_upload_start_time
        self.app = app
        self.msg = msg
        self.client_secrets_json = client_secrets_json
        self.token_file = token_file
        self.root_folder_id = GDRIVE_CONFIG.root_folder_id
        self.gauth = gauth
        self.drive = None

    def authenticate(self):
        self.gauth.LoadClientConfigFile(self.client_secrets_json)
        self.gauth.LoadCredentialsFile(self.token_file)

        if self.gauth.credentials is None:
            self.gauth.GetAuthUrl()
            self.msg.edit("<b>Log In</b>")
            print("Log In Required")
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()

        self.gauth.SaveCredentialsFile(self.token_file)
        self.drive = GoogleDrive(self.gauth)

    def create_or_get_folder(self, parent_folder_id, folder_name):
        file_list = self.drive.ListFile({
            "q": f"'{parent_folder_id}' in parents and title='{folder_name}' and trashed=false"
        }).GetList()

        if not file_list:
            return self._create_folder_in_parent(parent_folder_id, folder_name)
        else:
            return file_list[0]["id"]

    def _create_folder_in_parent(self, parent_folder_id, folder_name):
        folder_metadata = {
            "title": folder_name,
            "parents": [{"id": parent_folder_id}],
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder["id"]

    def upload_file(self, file_path, subfolder_path, ott="OTT"):
        if self.drive is None:
            self.authenticate()

        root_folder_id = self.root_folder_id
        subfolder_names = subfolder_path.split('/')
        current_parent_folder_id = root_folder_id

        for subfolder_name in subfolder_names:
            current_parent_folder_id = self.create_or_get_folder(
                current_parent_folder_id, subfolder_name)

        file_name = file_path.split("/")[-1]
        file_metadata = {"title": file_name, "parents": [
            {"id": current_parent_folder_id}]}

        file = self.drive.CreateFile(file_metadata)
        file.SetContentFile(file_path)
        file.Upload()

        
        try:
            file.InsertPermission(
            {"type": "anyone", "value": "anyone", "role": "reader"}) if GD_SHARER_CONFIG.is_making_drive_files_public else None
        except Exception:
            pass

        link = file["alternateLink"]

        print(f"File '{file_name}' uploaded successfully to Google Drive.")
        print(f"Link to the file: {link}")


        keyboard_buttons = []


        # Check if indexLink_format is not an empty string
        if GDRIVE_CONFIG.indexlink_format != "":

            indexLink = GDRIVE_CONFIG.indexlink_format.format(
                quote(subfolder_path), quote(file_name))

            drive_and_index_buttons = [
                InlineKeyboardButton("🔗 Drive URL", url=f"{link}"),
                InlineKeyboardButton("🚀 Index URL", url=f"{indexLink}")
            ]

            if GD_SHARER_CONFIG.is_uploading_to_filepress and GD_SHARER_CONFIG.filepress_connect_sid_cookie_value and GD_SHARER_CONFIG.filepress_connect_sid_cookie_value.strip():
                
                filepress_url = upload_to_filepress(link)
                keyboard_buttons.append(drive_and_index_buttons)

                if filepress_url is not None:

                    keyboard_buttons.append([
                        InlineKeyboardButton("🔗 Filepress URL", url=f"{filepress_url}")
                    ])
                else:
                    print("Filpress Upload for {} Failed check cookie value again".format(link))

            else:
                keyboard_buttons.append(drive_and_index_buttons)

        else:
            
            if GDRIVE_CONFIG.indexlink_format == "":
                drive_button = [
                InlineKeyboardButton("🔗 Drive URL", url=f"{link}")
            ]
                keyboard_buttons.append(drive_button)

            if GD_SHARER_CONFIG.is_uploading_to_filepress and GD_SHARER_CONFIG.filepress_connect_sid_cookie_value and GD_SHARER_CONFIG.filepress_connect_sid_cookie_value.strip():

                filepress_url = upload_to_filepress(link)
                
                if filepress_url is not None:
                    keyboard_buttons.append([
                        InlineKeyboardButton("🔗 Drive URL", url=f"{link}")
                    ])
                    # Append the Filepress URL button
                    keyboard_buttons.append([
                        InlineKeyboardButton("🔗 Filepress URL", url=f"{filepress_url}")
                    ])
                else:
                    print("Filpress Upload for {} Failed check cookie value again".format(link))
                



        inline_keyboard = InlineKeyboardMarkup(keyboard_buttons)



        caption = DL_DONE_MSG.format(
                get_readable_time(time.time() - self.c_time),
                file_name,
                ott,
                humanbytes(os.stat(file_name).st_size)
            )

        self.msg.edit(
            text=caption,
            reply_markup=inline_keyboard
        )

        try:
            os.remove(file_name)
        except:
            pass



# uploader = GoogleDriveUploader()
# uploader.upload_file("/content/sample_data/anscombe.json", "TEST98/TU/Work/79/")