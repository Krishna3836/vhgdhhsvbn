import subprocess
import threading
import time
import os
import requests
from bot.config import ytdlp, mp4decrypt, aria2c, proxies
from bot.config import UPLOAD_CONGIF
from bot.helpers.utils import parse_file_name
from bot.helpers.parser.mpd import MPD
from bot.helpers.utils import get_group_tag
from bot.config import PROXY_CONFIG, dl_folder
from bot.helpers.upload.gdrive import GoogleDriveUploader
from bot.helpers.upload.ftp import ftpUploader
from bot.helpers.upload.tg import tgUploader

class Processor():
    def __init__(self, app, message, link, key, video_resolution=None, video_quality=None, audio_codec=None, audio_quality=None, alang=None, fallback_language=None, init_file_name=None, ott=None, headers= None,  parse_subs = True):
        self.app = app
        self.message = message
        self.link = link
        self.key = key
        self.video_resolution = video_resolution
        self.video_quality = video_quality
        self.audio_codec = audio_codec
        self.audio_quality = audio_quality
        self.alang = alang
        self.fallback_language = fallback_language
        self.init_file_name = init_file_name
        self.ott = ott
        self.dl_headers = headers
        self.custom_group_tag = get_group_tag(str(self.message.from_user.id))

        self.process_start = time.time()
        self.end_code = str(time.time()).replace(".", "")

        
        self.msg = self.message.reply_text(f'''Processing...''')

        result, self.final_file_name = MPD(
            link, init_file_name, ott, self.custom_group_tag, parse_subs=parse_subs).refine(video_resolution=self.video_resolution, video_quality=self.video_quality, audio_codec=self.audio_codec, audio_quality=self.audio_quality, audio_languages=None, fallback_language=self.fallback_language)
        
        self.video_data = result.get('video')
        self.audio_data = result.get('audio')
        self.subtitles_data = result.get('subtitle')

        file_info = parse_file_name(init_file_name, video_resolution= "{}p".format(self.video_data['height']), GR = self.custom_group_tag)
        self.path = file_info.get('path')


    def download_audio_stream(self, stream_format, filename):
        dest = os.path.join(dl_folder, f"{filename}.m4a")
        try:
            cmd = [
                f"{ytdlp}"
            ]

            if PROXY_CONFIG.proxy_url and PROXY_CONFIG.proxy_url.strip() and PROXY_CONFIG.USE_PROXY_WHILE_DOWNLOADING:  # Check if PROXY_CONFIG.proxy_url is not empty or None
                cmd.extend(["--proxy", PROXY_CONFIG.proxy_url])

            

            cmd.extend(["--allow-unplayable-formats",
                        "-f", str(stream_format)])
            


            if self.dl_headers is not None:
                for key, value in self.dl_headers.items():
                    cmd.extend(["--add-headers", f'{key}:{value}'])
                        


            cmd.extend(
                [
                    "--geo-bypass-country",
                    "IN",
                    f"{self.link}",
                    "-o",
                    dest,
                    "--external-downloader",
                    f"{aria2c}",
                ])


            dl_process = subprocess.Popen(cmd)
            dl_process.wait()
        except Exception as e:
            self.msg.edit(f"Error Running YT-DLP Command {e}")
            return

    def mpd_download(self):
        threads = []

        for i, audio_info in enumerate(self.audio_data):
            stream_format = audio_info["id"]
            filename = f"enc_{stream_format}_{self.end_code}"
            thread = threading.Thread(
                target=self.download_audio_stream, args=(
                    stream_format, filename)
            )
            threads.append(thread)
            thread.start()
            print(
                f"[+] Downloading Audio Stream {i + 1} of {len(self.audio_data)}")

        try:
            video_format = self.video_data["id"]
            dest = os.path.join(
                dl_folder, f"enc_{video_format}_{self.end_code}.mp4")
            
            
            video_cmd = [
                f"{ytdlp}",
            ]

            if PROXY_CONFIG.proxy_url and PROXY_CONFIG.proxy_url.strip() and PROXY_CONFIG.USE_PROXY_WHILE_DOWNLOADING:  # Check if PROXY_CONFIG.proxy_url is not empty or None
                video_cmd.extend(["--proxy", PROXY_CONFIG.proxy_url])


            if self.dl_headers is not None:
                for key, value in self.dl_headers.items():
                    video_cmd.extend(["--add-headers", f'{key}:{value}'])


            video_cmd.extend([
                "--geo-bypass-country",
                "IN",
                "--allow-unplayable-formats",
                "-f",
                str(video_format),
                f"{self.link}",
                "-o",
                dest,
                "--external-downloader",
                f"{aria2c}",
            ])

            print("[+] Downloading Video Stream")
            subprocess.call(video_cmd)
        except Exception as e:
            self.msg.edit(f"Error Downloading Video File {e}")
            return

        for thread in threads:
            thread.join()

        return self.end_code

    def decrypt(self):
        try:
            for audio_info in self.audio_data:
                stream_format = audio_info["id"]
                enc_dl_audio_file_name = os.path.join(
                    dl_folder, f"enc_{stream_format}_{self.end_code}.m4a")
                dec_out_audio_file_name = os.path.join(
                    dl_folder, f"dec_{stream_format}_{self.end_code}.m4a")

                if isinstance(self.key, list):
                    cmd_audio_decrypt = [
                        f"{mp4decrypt}"]

                    for k in self.key:
                        cmd_audio_decrypt.append(str("--key"))
                        cmd_audio_decrypt.append(str(k))

                    cmd_audio_decrypt.append(str(enc_dl_audio_file_name)),
                    cmd_audio_decrypt.append(str(dec_out_audio_file_name))

                else:

                    cmd_audio_decrypt = [
                        f"{mp4decrypt}",
                        "--key",
                        str(self.key),
                        str(enc_dl_audio_file_name),
                        str(dec_out_audio_file_name)

                    ]
                subprocess.run(cmd_audio_decrypt, stdout=subprocess.DEVNULL)
                try:
                    os.remove(enc_dl_audio_file_name)
                except:
                    pass

            video_format = self.video_data["id"]
            enc_dl_video_file_name = os.path.join(
                dl_folder, f"enc_{video_format}_{self.end_code}.mp4")
            dec_out_video_file_name = os.path.join(
                dl_folder, f"dec_{video_format}_{self.end_code}.mp4")

            cmd_video_decrypt = [f"{mp4decrypt}"]
            if isinstance(self.key, list):
                cmd_video_decrypt = [
                    f"{mp4decrypt}"]

                for k in self.key:
                    cmd_video_decrypt.append(str("--key"))
                    cmd_video_decrypt.append(str(k))

                cmd_video_decrypt.append(str(enc_dl_video_file_name)),
                cmd_video_decrypt.append(str(dec_out_video_file_name))

            else:
                cmd_video_decrypt = [
                    f"{mp4decrypt}",
                    "--key",
                    str(self.key),
                    str(enc_dl_video_file_name),
                    str(dec_out_video_file_name)

                ]
            try:
                subprocess.run(cmd_video_decrypt, stdout=subprocess.DEVNULL)
            except Exception as e:
                raise Exception(str(e))

            try:
                os.remove(enc_dl_video_file_name)
            except:
                pass

        except Exception as e:
            raise Exception("Error During Decryption")

        return self.end_code
    
    def dl_subs_v2(self):

        if self.subtitles_data is not None:

            for sub in self.subtitles_data:
                
                subs_lang = sub["lang"]
                subs_url = sub['baseURL']

                dest = os.path.join(
                    dl_folder, f"subtitle_{subs_lang}_{self.end_code}.vtt")


                print(f"[+] Downloading Subtitle - {subs_lang}")
                print(f"[+] URL - {subs_url}")

                request_headers = {
                    'user-agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
                }
                
                if self.dl_headers is not None:
                    for key, value in self.dl_headers.items():
                        request_headers[key] = value

                r = requests.get(subs_url, proxies=proxies, headers=request_headers, allow_redirects=True)
                open(dest, 'wb').write(r.content)

    def dl_subs(self):

        if self.subtitles_data is not None:

            for sub in self.subtitles_data:
                subs_lang = sub["lang"]
                subs_url = sub['baseURL'] + sub["url"]
                subs_dl_cmd = [
                    f"{ytdlp}",
                    "--geo-bypass-country",
                    "IN",
                    "--add-headers",
                    "user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                    f"{subs_url}",
                    "-o",
                    f"subtitle_{subs_lang}_{self.end_code}.vtt",
                    "--external-downloader",
                    f"{aria2c}"
                ]
                print(f"[+] Downloading Subtitle - {sub['lang']}")
                print(f"[+] URL - {subs_url}")
                subprocess.call(subs_dl_cmd)




    def mux_video(self, startTime=None, endTime=None):
        file_prefix = "enc" if self.key is None else "dec"

        dec_out_video_file_name = os.path.join(
            dl_folder, f"{file_prefix}_{self.video_data['id']}_{self.end_code}.mp4")
        audio_files = [
            os.path.join(
                dl_folder, f"{file_prefix}_{audio_info['id']}_{self.end_code}.m4a")
            for audio_info in self.audio_data
        ]

        ffmpeg_opts = ["ffmpeg", "-y"]

    # Input video file
        ffmpeg_opts.extend(["-i", dec_out_video_file_name])

    # Input audio files
        for audio_file in audio_files:
            ffmpeg_opts.extend(["-i", audio_file])

    # Input subtitle files
        if self.subtitles_data is not None:
            subs_files = [
                os.path.join(
                    dl_folder, f"subtitle_{sub['lang']}_{self.end_code}.vtt")
                for sub in self.subtitles_data
            ]
            for subs_file in subs_files:
                ffmpeg_opts.extend(["-i", subs_file])

    # Set start and end time if provided
        if startTime is not None and endTime is not None:
            ffmpeg_opts.extend(["-ss", f"{startTime}"])
            ffmpeg_opts.extend(["-to", f"{endTime}"])

    # Map streams
        ffmpeg_opts.extend(["-map", "0:v:0"])  # Video stream
        for i in range(len(self.audio_data)):
            ffmpeg_opts.extend(["-map", f"{i+1}:a:0"])  # Audio streams
        if self.subtitles_data is not None:
            for i in range(len(self.subtitles_data)):
                ffmpeg_opts.extend(["-map", f"{len(self.audio_data)+1+i}:s:0"])  # Subtitle streams

    # Set metadata
        ffmpeg_opts.extend(["-metadata", f"encoded_by={self.custom_group_tag}"])
        ffmpeg_opts.extend(["-metadata:s:a", f"title={self.custom_group_tag}"])
        ffmpeg_opts.extend(["-metadata:s:v", f"title={self.custom_group_tag}"])
        if self.subtitles_data is not None:
            ffmpeg_opts.extend(["-metadata:s:s", f"title={self.custom_group_tag}"])

    # Set language metadata for audio and subtitle streams
        for i, audio_info in enumerate(self.audio_data):
            lang = audio_info["lang"]
            ffmpeg_opts.extend(["-metadata:s:a:{0}".format(i), f"language={lang}"])
        if self.subtitles_data is not None:
            for i in range(len(self.subtitles_data)):
                ffmpeg_opts.extend(["-metadata:s:s:{0}".format(i), f"language={self.subtitles_data[i]['lang']}"])

    # Output file
        out_name = f"{self.end_code}.mkv"
        ffmpeg_opts.extend(["-c", "copy", out_name])

        try:
            print("Running ffmpeg command:")
            print(" ".join(ffmpeg_opts))
            subprocess.check_call(ffmpeg_opts)
        except subprocess.CalledProcessError as e:
            print(f"FFMPEG Error: {e.returncode} - {e.output}")
            raise

        try:
            os.rename(out_name, self.final_file_name)
        except OSError as e:
            raise Exception(f"OSError: {e.filename} - {e.strerror}")

    # Clean up temporary files
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except OSError as e:
                    print(f"Error removing file: {e.filename} - {e.strerror}")
                    pass
        if os.path.exists(dec_out_video_file_name):
            try:
                os.remove(dec_out_video_file_name)
            except OSError as e:
                print(f"Error removing file: {e.filename} - {e.strerror}")
                pass

        return self.final_file_name



    

    def start_process(self, startTime=None, endTime=None):
        task_start_time = time.time()
        self.msg.edit(
            '<code>[+]</code> <b>Downloading</b>\n<code>{}</code>'.format(self.final_file_name))
        
        self.dl_subs_v2()
        self.mpd_download()


        self.msg.edit('<code>[+]</code> <b>Decrypting</b>\n<code>{}</code>\n\n<code>[+]</code> <b>Using Keys\n<code>{}</code></b>'.format(
            self.final_file_name, "\n".join(self.key) if isinstance(self.key, list) else self.key))


        if self.key is not None:
            self.decrypt()


        self.msg.edit(
            '<code>[+]</code> <b>Muxing</b>\n<code>{}</code>'.format(self.final_file_name))

        out_file_name = self.mux_video(startTime, endTime)

        

        self.msg.edit(
            '<code>[+]</code> <b>Uploading</b>\n<code>{}</code>'.format(self.final_file_name))
        
        upload_path = "BOT Uploads/{}/{}".format(self.ott, self.path)


        upload_to = UPLOAD_CONGIF.upload_to.lower() if UPLOAD_CONGIF.upload_to.lower() in ['tg', 'ftp', 'gdrive'] else UPLOAD_CONGIF.default_upload_to

        if upload_to == "tg":
            uploader = tgUploader(self.app, self.msg)
            uploader.upload_file(out_file_name)

        elif upload_to == "ftp":
            uploader = ftpUploader(self.app, self.msg, task_start_time)
            uploader.upload_file(out_file_name, upload_path, ott=self.ott)

        elif upload_to == "gdrive":
            uploader = GoogleDriveUploader(self.app, self.msg, task_start_time)
            uploader.upload_file(out_file_name, upload_path, ott=self.ott)


        return out_file_name
