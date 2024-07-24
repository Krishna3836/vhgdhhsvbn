from bot.config import FILENAME_CONFIG
from bot.helpers.utils import language_mapping
import re






class Filename:
    def __init__(self, data, init_file_name, ott, custom_group_tag):
        self.audioslist = data.get('audio')
        self.videoslist = data.get('video')
        self.subtitleslist = data.get('subtitle')
        self.init_file_name = init_file_name
        self.GR = custom_group_tag
        self.ott = ott
        self.language_order = FILENAME_CONFIG.language_order
        self.is_release_year_available, self.release_year, self.movie_title = self.is_release_year_available(self.init_file_name)

    def is_release_year_available(self, text):
        words = text.split()
        last_word = words[-1]

        has_season_episode_format = re.search(r'\bS\d{2}E\d{2}\b', text) is not None

        try:
            release_year = int(last_word)

            if len(str(release_year)) == 4 and has_season_episode_format is False:
                movie_name = " ".join(words[:-1])
                return True, release_year, movie_name
            else:
                return False, " ".join(words), "N/A"
        except ValueError:
            return False, " ".join(words), "N/A"

    def get_subtitle_write_data(self):

        if self.subtitleslist is not None and len(self.subtitleslist) != 0:
            if len(self.subtitleslist) == 1:
                subtitle_language_suffix = [char for char in self.subtitleslist[0].get('lang')][0].upper()
                subs_write = f"{subtitle_language_suffix}Sub"
            else:
                subs_write = "MSubs"
        else:
            subs_write = ""

        return subs_write

    def _group_unique_audio_configs(self):
        unique_audio_configs = {}
        for audio in self.audioslist:
            audio_codec_release_name = "{}{}{}".format(audio['codec_general'], audio['channels'], ((".ATMOS" if FILENAME_CONFIG.filename_format == "p2p" else " ATMOS") if audio['joc'] is not None else ""))
            bandwidth_release_name = "{}".format(str(audio['bitrate_general']) +  (FILENAME_CONFIG.p2p_audio_bitrate if FILENAME_CONFIG.filename_format ==
                           "p2p" else FILENAME_CONFIG.non_p2p_audio_bitrate))

            config = (audio_codec_release_name.rsplit(
                '.', 1)[0], bandwidth_release_name)

            if config not in unique_audio_configs:
                unique_audio_configs[config] = []
            unique_audio_configs[config].append(audio)
        return unique_audio_configs

    def _custom_sort_key(self, lang):
        return self.language_order.index(lang)

    def _group_languages_by_audio_config(self):
        unique_audio_configs = self._group_unique_audio_configs()
        audio_groups = {}
        for config, audio_data in unique_audio_configs.items():
            langs = sorted(
                set([audio['lang'] for audio in audio_data]), key=self._custom_sort_key)
            # lang_concatenated = "-".join(langs)
            lang_concatenated = "-".join(langs)
            audio_groups[lang_concatenated] = audio_data
        return audio_groups


    def _generate_languages_parts(self):
        audio_groups = self._group_languages_by_audio_config() if self.audioslist[0]['lang'] is not None else None

        if audio_groups is None:
            return None

        filename_parts = []

        for lang_group, audio_data in audio_groups.items():
            audio_codec_release_name = "{codec} {channel} {atmos_part}".format(
            codec = audio_data[0]['codec_general'],
            channel = audio_data[0]['channels'],
            atmos_part = (("ATMOS" if FILENAME_CONFIG.filename_format == "p2p" else "ATMOS") if audio_data[0]['joc'] is not None else "")
        )
            audio_codec_release_name = audio_codec_release_name.replace(" ", "") if FILENAME_CONFIG.filename_format == "p2p" else audio_codec_release_name

            lang_group = [language_mapping(
                lang.strip(), "639-2").upper() for lang in lang_group.split("-")]


            if FILENAME_CONFIG.filename_format == "p2p":
                lang_group = "-".join(lang_group)
            else:
                lang_group = " + ".join(lang_group)


            if FILENAME_CONFIG.filename_format == "p2p":
                filename_parts.append(lang_group)
            else:
                filename_parts.append(lang_group)


        return filename_parts

    def _generate_audio_codec_parts(self):
        audio_groups = self._group_languages_by_audio_config() if self.audioslist[0]['lang'] is not None else None
        if audio_groups is None:
            if FILENAME_CONFIG.filename_format == "p2p":
                self.audio_codec_name = f"{self.audioslist[0]['codec_general']}.{self.audioslist[0]['channels']}"
            else:
                self.audio_codec_name = f"({self.audioslist[0]['codec_general']}{self.audioslist[0]['channels']} - {str(self.audioslist[0]['bitrate_general'])} {FILENAME_CONFIG.p2p_audio_bitrate if FILENAME_CONFIG.filename_format == 'p2p' else FILENAME_CONFIG.non_p2p_audio_bitrate}) "
            return None
        filename_parts = []

        for lang_group, audio_data in audio_groups.items():
            audio_codec_release_name = "{codec} {channel} {atmos_part}".format(
                codec = audio_data[0]['codec_general'],
                channel = audio_data[0]['channels'],
                atmos_part = ((".ATMOS" if FILENAME_CONFIG.filename_format == "p2p" else "ATMOS") if audio_data[0]['joc'] is not None else "")
            )
            audio_codec_release_name = audio_codec_release_name.replace(" ", "") if FILENAME_CONFIG.filename_format == "p2p" else audio_codec_release_name

            bandwidth_release_name = "{}".format(str(audio_data[0]['bitrate_general']) +  (FILENAME_CONFIG.p2p_audio_bitrate if FILENAME_CONFIG.filename_format ==
                              "p2p" else FILENAME_CONFIG.non_p2p_audio_bitrate))

            if FILENAME_CONFIG.filename_format == "p2p":
                filename_parts.append(
                    f"{audio_codec_release_name}.{bandwidth_release_name}")
            else:
                filename_parts.append(
                    f"({audio_codec_release_name} - {bandwidth_release_name})")
        return filename_parts

    def language_and_audio_parts(self):
        audio_groups = self._group_languages_by_audio_config() if self.audioslist[0]['lang'] is not None else None
        if audio_groups is None:
            return None
        filename_parts = []


        for lang_group, audio_data in audio_groups.items():
            audio_codec_release_name = "{codec} {channel} {atmos_part}".format(
                codec = audio_data[0]['codec_general'],
                channel = audio_data[0]['channels'],
                atmos_part = ((".ATMOS" if FILENAME_CONFIG.filename_format == "p2p" else "ATMOS") if audio_data[0]['joc'] is not None else "")
            )
            audio_codec_release_name = audio_codec_release_name.replace(" ", "") if FILENAME_CONFIG.filename_format == "p2p" else audio_codec_release_name

            bandwidth_release_name = "{}".format(str(audio_data[0]['bitrate_general']) +  (FILENAME_CONFIG.p2p_audio_bitrate if FILENAME_CONFIG.filename_format ==
                              "p2p" else FILENAME_CONFIG.non_p2p_audio_bitrate))

            lang_group = [language_mapping(
                lang.strip(), "639-2").upper() for lang in lang_group.split("-")]
            if FILENAME_CONFIG.filename_format == "p2p":
                lang_group = "-".join(lang_group)
            else:
                lang_group = " + ".join(lang_group)

            if FILENAME_CONFIG.filename_format == "p2p":
                filename_parts.append(
                    f"{lang_group}.{audio_codec_release_name}.{bandwidth_release_name}")
            else:
                filename_parts.append(
                     f"{lang_group} ({audio_codec_release_name} - {bandwidth_release_name})")
        return filename_parts


    def generate_filename_v2(self):

        subtitle_write_data = self.get_subtitle_write_data()
        language_and_audio_parts = self.language_and_audio_parts()


        video_codec = self.videoslist['codec_general']
        range = self.videoslist['range'] if not self.videoslist['range'] == "SDR" else ""
        bit_depth = self.videoslist['bit_depth']
        video_resolution = f"{self.videoslist['height']}p"

        video_quality = self.videoslist.get('quality') if self.videoslist.get('quality') is not None and self.videoslist.get('quality') != "NA" else ""

        video_codec = f"{video_codec}"

        video_codec_p2p = f"{video_codec}-{bit_depth}bit" if bit_depth == 10 else video_codec

        video_codec_non_p2p = "x264" if video_codec == "H264" else (
            "x265" + (" 10bit" if bit_depth == 10 else "") if "H.265" or "HEVC" in video_codec else "")

        if FILENAME_CONFIG.filename_format == "p2p":
            init_file_name = self.init_file_name.replace(" ", ".")
            if language_and_audio_parts is not None:
                filename = f"{init_file_name}.{video_resolution}.{video_quality}.{self.ott}.WEB-DL.{'-'.join(language_and_audio_parts)}.{video_codec_p2p}.{range}.{subtitle_write_data}-{self.GR}.mkv"
            else:
                filename = f"{init_file_name}.{video_resolution}.{video_quality}.{self.ott}.WEB-DL.{self.audio_codec_name}.{video_codec_p2p}.{range}.{subtitle_write_data}-{self.GR}.mkv"


        else:
              non_p2p_init_file_name = f"{self.movie_title} ({self.release_year})" if self.is_release_year_available else self.init_file_name
              if language_and_audio_parts is not None:
                  filename = f"{non_p2p_init_file_name} {video_resolution} {video_quality} {self.ott} WEB-DL {video_codec_non_p2p} {range} [{' - '.join(language_and_audio_parts)}] {subtitle_write_data} {FILENAME_CONFIG.underscore_before_after_group_tag}{self.GR}{FILENAME_CONFIG.underscore_before_after_group_tag}.mkv"
              else:
                  filename = f"{non_p2p_init_file_name} {video_resolution} {video_quality} {self.ott} WEB-DL {video_codec_non_p2p} {range} {self.audio_codec_name} {subtitle_write_data} {FILENAME_CONFIG.underscore_before_after_group_tag}{self.GR}{FILENAME_CONFIG.underscore_before_after_group_tag}.mkv"

        return self.sanitize(filename)


    def sanitize(self, text):
        text = re.sub(r'\.+', '.', text)
        return ' '.join(text.split()).replace(".-", '-')