import re, base64
from bot.config import FILENAME_CONFIG
from bot.helpers.utils import language_mapping, custom_sort
from bot.helpers.filename import Filename
from bot.helpers.pssh import get_mpd_text, extract_pssh
import requests
from lxml import etree
from typing import Optional, Any
from functools import partial
from typing import Any, Optional, Union
import json
from lxml.etree import Element
import re
from enum import Enum


def mpd_table(url, init_file_name, ott, keys, lic_url):

    result = MPD(
        url, init_file_name, ott, custom_group_tag=FILENAME_CONFIG.default_group_tag).parse()
    audioslist = result.get('audio')
    videoslist = result.get('video')
    subtitlelist = result.get('subtitle')

    table_audio_data = ['- {language} ({languageCode}) [{formatID}] [{audio_info}]'.format(
        language=language_mapping(audio['lang'], return_key="en") if audio['lang'] else "NA",
        languageCode=audio['lang'],
        formatID=audio['id'],
        audio_info=audio['codec_general'] + str(audio['channels']) +
        f" - {audio['bitrate_general']}Kbps"

    ) for audio in audioslist]

    table_videos_list = ['- {resolution} {vcodec} [{formatID}] - {bandwidth}Kbps'.format(
        resolution="{}x{}".format(video['width'], video['height']),
        vcodec=video['codec_general'],
        formatID=video['id'],
        bandwidth=int(video['bitrate']) / 1000
    ) for video in videoslist]

    if subtitlelist is not None:
        table_subs_list = ['- {lang}'.format(
            lang=subtitle.get('lang'),
            url=subtitle.get('url')
        ) for subtitle in subtitlelist]

    else:
        table_subs_list = None

    table = ''

    if table_audio_data:
        table += 'Audio:\n'
        table += '\n'.join(table_audio_data) + '\n\n'

    if table_videos_list:
        table += 'Video:\n'
        table += '\n'.join(table_videos_list) + '\n\n'

    if table_subs_list:
        table += 'Subtitle:\n'
        table += '\n'.join(table_subs_list) + '\n\n'

    if keys:
        table += 'KEYS:\n'
        table += "\n".join(keys) + "\n\n" if isinstance(keys,
                                                        list) else keys + '\n\n'

    table += 'MPD URL:\n'
    table += url + '\n\n'
    
    if lic_url:
        table += 'LICENSE URL:\n'
        table += lic_url + '\n\n'

    return table


def load_xml(xml: Union[str, bytes]) -> etree.ElementTree:
    """Safely parse XML data to an ElementTree, without namespaces in tags."""
    if not isinstance(xml, bytes):
        xml = xml.encode("utf8")
    root = etree.fromstring(xml)
    for elem in root.getiterator():
        if not hasattr(elem.tag, "find"):
            # e.g. comment elements
            continue
        elem.tag = etree.QName(elem).localname
        for name, value in elem.attrib.items():
            local_name = etree.QName(name).localname
            if local_name == name:
                continue
            del elem.attrib[name]
            elem.attrib[local_name] = value
    etree.cleanup_namespaces(root)
    return root

class Range(str, Enum):
        SDR = "SDR"        # No Dynamic Range
        HLG = "HLG"        # https://en.wikipedia.org/wiki/Hybrid_log%E2%80%93gamma
        HDR10 = "HDR10"    # https://en.wikipedia.org/wiki/HDR10
        HDR10P = "HDR10+"  # https://en.wikipedia.org/wiki/HDR10%2B
        DV = "DV"          # https://en.wikipedia.org/wiki/Dolby_Vision

        @staticmethod
        def from_cicp(primaries: int, transfer: int, matrix: int):
            """
            ISO/IEC 23001-8 Coding-independent code points to Video Range.

            Sources:
            https://www.itu.int/rec/T-REC-H.Sup19-202104-I
            """
            class Primaries(Enum):
                Unspecified = 0
                BT_709 = 1
                BT_601_625 = 5
                BT_601_525 = 6
                BT_2020_and_2100 = 9
                SMPTE_ST_2113_and_EG_4321 = 12  # P3D65

            class Transfer(Enum):
                Unspecified = 0
                BT_709 = 1
                BT_601 = 6
                BT_2020 = 14
                BT_2100 = 15
                BT_2100_PQ = 16
                BT_2100_HLG = 18

            class Matrix(Enum):
                RGB = 0
                YCbCr_BT_709 = 1
                YCbCr_BT_601_625 = 5
                YCbCr_BT_601_525 = 6
                YCbCr_BT_2020_and_2100 = 9  # YCbCr BT.2100 shares the same CP
                ICtCp_BT_2100 = 14

            primaries = Primaries(primaries)
            transfer = Transfer(transfer)
            matrix = Matrix(matrix)

            # primaries and matrix does not strictly correlate to a range

            if (primaries, transfer, matrix) == (0, 0, 0):
                return Range.SDR
            elif primaries in (Primaries.BT_601_625, Primaries.BT_601_525):
                return Range.SDR
            elif transfer == Transfer.BT_2100_PQ:
                return Range.HDR10
            elif transfer == Transfer.BT_2100_HLG:
                return Range.HLG
            else:
                return Range.SDR


class MPD:
    @classmethod
    def __init__(self, url, init_file_name, ott, custom_group_tag = FILENAME_CONFIG.default_group_tag, parse_subs = True):
        self.ott = ott
        self.init_file_name = init_file_name
        self.custom_group_tag = custom_group_tag
        self.url = url
        self.parse_subs = parse_subs

    @staticmethod
    def _get(item: str, adaptation_set: etree.Element, representation: Optional[etree.Element] = None) -> Optional[Any]:
        """Helper to get a requested item from the Representation, otherwise from the AdaptationSet."""
        adaptation_set_item = adaptation_set.get(item)
        if representation is None:
            return adaptation_set_item

        representation_item = representation.get(item)
        if representation_item is not None:
            return representation_item

        return adaptation_set_item

    @staticmethod
    def ReplaceCodeLanguages(X):
        X = X.lower()
        X = X.replace('_subtitle_dialog_0', '').replace('_narrative_dialog_0', '').replace('_caption_dialog_0', '').replace('_dialog_0', '').replace('_descriptive_0', '_descriptive').replace('_descriptive', '_descriptive').replace('_sdh', '-sdh').replace('es-es', 'es').replace('SPA', 'es').replace('en-es', 'es').replace('kn-in', 'kn').replace('gu-in', 'gu').replace('ja-jp', 'ja').replace('mni-in', 'mni').replace('si-in', 'si').replace('as-in', 'as').replace('ml-in', 'ml').replace('sv-se', 'sv').replace('hy-hy', 'hy').replace('sv-sv', 'sv').replace('da-da', 'da').replace('fi-fi', 'fi').replace('nb-nb', 'nb').replace('is-is', 'is').replace('uk-uk', 'uk').replace('hu-hu', 'hu').replace('bg-bg', 'bg').replace('hr-hr', 'hr').replace('lt-lt', 'lt').replace('et-et', 'et').replace('el-el', 'el').replace('he-he', 'he').replace('ar-ar', 'ar').replace('fa-fa', 'fa').replace('ENG', 'en').replace('ro-ro', 'ro').replace('sr-sr', 'sr').replace('cs-cs', 'cs').replace('sk-sk', 'sk').replace('mk-mk', 'mk').replace('hi-hi', 'hi').replace('bn-bn', 'bn').replace('ur-ur', 'ur').replace('pa-pa', 'pa').replace('ta-ta', 'ta').replace('te-te', 'te').replace('mr-mr', 'mr').replace('kn-kn', 'kn').replace('gu-gu', 'gu').replace('ml-ml', 'ml').replace('si-si', 'si').replace('as-as', 'as').replace('mni-mni', 'mni').replace('tl-tl', 'tl').replace('id-id','id').replace('ms-ms', 'ms').replace('vi-vi', 'vi').replace('th-th', 'th').replace('km-km', 'km').replace('ko-ko', 'ko').replace('zh-zh', 'zh').replace('ja-ja', 'ja').replace('ru-ru', 'ru').replace('tr-tr', 'tr').replace('it-it', 'it').replace('es-mx', 'es-la').replace('ar-sa', 'ar').replace('zh-cn', 'zh').replace('nl-nl', 'nl').replace('pl-pl', 'pl').replace('pt-pt', 'pt').replace('hi-in', 'hi').replace('mr-in', 'mr').replace('bn-in', 'bn').replace('te-in', 'te').replace('POR', 'pt').replace('cmn-hans', 'zh-hans').replace('cmn-hant', 'zh-hant').replace('ko-kr', 'ko').replace('en-au', 'en').replace('es-419', 'es-la').replace('es-us', 'es-la').replace('en-us', 'en').replace('en-gb', 'en').replace('fr-fr', 'fr').replace('de-de', 'de').replace('las-419', 'es-la').replace('ar-ae', 'ar').replace('da-dk', 'da').replace('yue-hant', 'yue').replace('bn-in', 'bn').replace('ur-in', 'ur').replace('ta-in', 'ta').replace('sl-si', 'sl').replace('cs-cz', 'cs').replace('hi-jp', 'hi').replace('-001', '').replace('en-US', 'en').replace('deu', 'de').replace('eng', 'en').replace('ca-es', 'cat').replace('fil-ph', 'fil').replace('en-ca', 'en').replace('eu-es', 'eu').replace('ar-eg', 'ar').replace('he-il', 'he').replace('el-gr', 'he').replace('nb-no', 'nb').replace('es-ar', 'es-la').replace('en-ph', 'en').replace('sq-al', 'sq').replace('bs-ba', 'bs')
        return X

    @staticmethod
    def _findall(tag: str, adaptation_set: etree.Element, representation: Optional[etree.Element] = None, both: bool = False):
        """Helper to find all elements with a tag in the Representation, otherwise in the AdaptationSet."""
        if representation is not None and both:
            return adaptation_set.findall(".//" + tag) + representation.findall(".//" + tag)
        elif representation is not None:
            return representation.findall(".//" + tag)
        else:
            return adaptation_set.findall(".//" + tag)

    @staticmethod
    def get_ddp_complexity_index(adaptation_set: etree.Element, representation: Optional[etree.Element]) -> Optional[int]:
        """Get the DD+ Complexity Index (if any) from the AdaptationSet or Representation."""
        return next((
            int(x.get("value"))
            for x in MPD._findall("SupplementalProperty", adaptation_set, representation, both=True)
            if x.get("schemeIdUri") == "tag:dolby.com,2018:dash:EC3_ExtensionComplexityIndex:2018"
        ), None)

    @staticmethod
    def parse_channels(channels: Union[str, int, float]) -> float:
        """Converts a Channel string to a float representing audio channel count and layout."""
        if isinstance(channels, str):
            # TODO: Support all possible DASH channel configurations (https://datatracker.ietf.org/doc/html/rfc8216)
            if channels.upper() == "A000":
                return 2.0
            elif channels.upper() == "F801":
                return 5.1
            elif channels.replace("ch", "").replace(".", "", 1).isdigit():
                # e.g., '2ch', '2', '2.0', '5.1ch', '5.1'
                return float(channels.replace("ch", ""))
            raise NotImplementedError(f"Unsupported Channels string value, '{channels}'")
        return channels

    @staticmethod
    def round_bitrate(bitrate: int) -> int:
        bits = [786, 640, 448, 384, 192, 128, 96, 64, 32]
        nearest_bitrate = min(bits, key=lambda x: abs(x - bitrate))
        return nearest_bitrate

    @staticmethod
    def audio_mime_convert(mime: str) -> str:
        mime = mime.lower().strip().split(".")[0]
        if mime == "mp4a":
          return "AAC"
        if mime == "ac-3":
          return "DD"
        if mime == "ec-3":
          return "DD+"
        if mime == "opus":
          return "OPUS"
        if mime == "dtsc":
          return "DTS"
        if mime == "alac":
          return "ALAC"
        if mime == "flac":
          return "FLAC"
        raise ValueError(f"The MIME '{mime}' is not a supported Audio Codec")

    @staticmethod
    def get_bit_depth(codec: str) -> str:
        codec = codec.lower().strip()

        if "hev1.2" in codec:
            return 10
        return 8

    @staticmethod
    def video_mime_convert(mime: str) -> str:
        mime = mime.lower().strip().split(".")[0]
        if mime in (
                "avc1", "avc2", "avc3",
                "dva1", "dvav",  # Dolby Vision
            ):
            return "H264"

        if mime in (
                "hev1", "hev2", "hev3", "hvc1", "hvc2", "hvc3",
                "dvh1", "dvhe",  # Dolby Vision
                "lhv1", "lhe1",  # Layered
            ):
            return "HEVC"

        if mime == "vc-1":
            return "VC-1"

        if mime in ("vp08", "vp8"):
            return "VP8"

        if mime in ("vp09", "vp9"):
            return "VP9"

        if mime == "av01":
            return "AV1"

        raise ValueError(f"The MIME '{mime}' is not a supported Video Codec")

    @staticmethod
    def is_descriptive(adaptation_set: etree.Element) -> bool:
        """Check if the AdaptationSet is descriptive."""
        roles = set(x.get("value") for x in MPD._findall("Role", adaptation_set))
        return "descriptive" in roles

    @staticmethod
    def get_video_range(
        codecs: str,
        all_supplemental_props: list[Element],
        all_essential_props: list[Element]
    ) -> Range:
        if codecs.startswith(("dva1", "dvav", "dvhe", "dvh1")):
            return Range.DV

        return Range.from_cicp(
            primaries=next((
                int(x.get("value"))
                for x in all_supplemental_props + all_essential_props
                if x.get("schemeIdUri") == "urn:mpeg:mpegB:cicp:ColourPrimaries"
            ), 0),
            transfer=next((
                int(x.get("value"))
                for x in all_supplemental_props + all_essential_props
                if x.get("schemeIdUri") == "urn:mpeg:mpegB:cicp:TransferCharacteristics"
            ), 0),
            matrix=next((
                int(x.get("value"))
                for x in all_supplemental_props + all_essential_props
                if x.get("schemeIdUri") == "urn:mpeg:mpegB:cicp:MatrixCoefficients"
            ), 0)
        )



    @classmethod
    def parse(self, headers = None, fallback_language = None):

        CHANNEL_MAP = {5.1: 5.1, 6.0: 5.1, 6: 5.1,
                            2.0:  2.0, 2:  2.0, 1.0:  2.0, 1:  2.0}

        url = self.url
        self.session = requests.Session()

        # if headers:
        #       self.session.headers.update(headers)

        text = get_mpd_text(self.url)
        
        manifest = load_xml(text)

        audioslist, videoslist, subtitleslist = list(), list(), list()


        for period in manifest.findall("Period"):
            for adaptation_set in period.findall("AdaptationSet"):
                for rep in adaptation_set.findall("Representation"):
                    get = partial(self._get, adaptation_set=adaptation_set, representation=rep)
                    findall = partial(self._findall, adaptation_set=adaptation_set, representation=rep, both=True)


                    codecs = get("codecs")
                    content_type = get("contentType")
                    mime_type = get("mimeType")

                    if not content_type and mime_type:
                        content_type = mime_type.split("/")[0]
                    if not content_type and not mime_type:
                        raise ValueError("Unable to determine the format of a Representation, cannot continue...")

                    if content_type == "video":
                        fileURL = url.rsplit('/', 1)[0] + '/' + rep.find("BaseURL").text.rsplit('/', 1)[-1] if rep.find("BaseURL") else "NA"
                        track_args = dict(
                            range = self.get_video_range(
                                codecs,
                                findall("SupplementalProperty"),
                                findall("EssentialProperty")
                            ),
                            bitrate=get("bandwidth") or None,
                            fileURL = fileURL,
                            width=get("width") or 0,
                            height=get("height") or 0,
                            bit_depth = self.get_bit_depth(get("codecs")),
                            codec=get("codecs") or None,
                            codec_general = self.video_mime_convert(get("codecs") or "mp4a.40.2"),
                            id=get("id").replace("/", "_") or None,
                            fps=get("frameRate") or (rep.find("SegmentBase") or {}).get("timescale") or None
                        )
                        videoslist.append(track_args)

                    if content_type == "audio":
                        fileURL = url.rsplit('/', 1)[0] + '/' + rep.find("BaseURL").text.rsplit('/', 1)[-1] if rep.find("BaseURL") else ""

                        lang = fallback_language if fallback_language is not None else (language_mapping(self.ReplaceCodeLanguages(get("lang"))) if get("lang") is not None else None)


                        track_args = dict(
                            lang = lang,
                            codec = get("codecs") or "mp4a.40.2",
                            bitrate=int(get("bandwidth")) or None,
                            bitrate_general= self.round_bitrate(int(get("bandwidth")) / 1000),
                            fileURL = fileURL,
                            channels=CHANNEL_MAP.get(self.parse_channels(next(iter(
                                rep.xpath("AudioChannelConfiguration/@value")
                                or adaptation_set.xpath("AudioChannelConfiguration/@value")
                            ), None))),
                            codec_general = self.audio_mime_convert(get("codecs") or "mp4a.40.2"),
                            id=get("id").replace("/", "_") or None,
                            joc=self.get_ddp_complexity_index(adaptation_set, rep),
                            descriptive=self.is_descriptive(adaptation_set)
                        )


                        audioslist.append(track_args)

                    if content_type == "text":
                        id = rep.find("BaseURL").text if rep.find("BaseURL") is not None else get("id")
                        baseurl = re.sub(r'[^\/]*$', '', url)
                        track_args = dict(
                            lang = get("lang") or None,
                            baseURL = baseurl + id
                        )
                        subtitleslist.append(track_args)

        self.result = {
            "video" : videoslist,
            "audio" : audioslist,
            "subtitle" : subtitleslist if self.parse_subs is True else None,
        }

        return self.result

    @classmethod
    def find_mid_value(self, data_list, key):
        sorted_data = sorted(data_list, key=lambda x: int(x[key]))
        middle_index = len(sorted_data) // 2
        return sorted_data[middle_index]

    @classmethod
    def filter_audio_quality(self, audioslist, audio_quality):
        audio_quality = audio_quality.upper().strip()
        lang_groups = {}  # Dictionary to group audio items by lang

        for audio in audioslist:
            lang = audio["lang"]
            if lang not in lang_groups:
                lang_groups[lang] = []
            lang_groups[lang].append(audio)

        filtered_audios = []

        for lang, audio_group in lang_groups.items():
            if audio_quality == "HQ":
                selected_audio = max(
                    audio_group, key=lambda x: int(x["bitrate"]))
            elif audio_quality == "MQ":
                selected_audio = self.find_mid_value(audioslist, 'bitrate')
            elif audio_quality == "LQ":
                selected_audio = min(
                    audio_group, key=lambda x: int(x["bitrate"]))
            else:
                # Default to "HQ" if no audio_quality is specified
                selected_audio = max(
                    audio_group, key=lambda x: int(x["bitrate"]))

            filtered_audios.append(selected_audio)

        return filtered_audios

    @classmethod
    def refine(self, video_resolution=None, video_quality="HQ", audio_languages=None, audio_codec=None, audio_quality="HQ", fallback_language=None):

        AUDIO_CODEC_v2_MAP = {
            "aac": "mp4a.40.2",
            "dd": "ac-3",
            "dd+": "ec-3",
            "dolby": "ac-3",
            "dolbydigital+": "ec-3",
            "ddplus": "ec-3",
            "mp4a.40.2": "mp4a.40.2",
            "ac-3": "ac-3",
            "ec-3": "ec-3"
        }

        self.parse(self.url, fallback_language=fallback_language)

        video_quality = video_quality.upper().strip() if video_quality is not None else None
        video_resolution = video_resolution.replace("p", "").strip() if video_resolution is not None else max(self.result.get('video'), key=lambda x: int(x["height"])).get('height')


        # VIDEO RESOLUTION
        if video_resolution:
            filtered_video_data = [
                video
                for video in self.result.get('video')
                if int(video["height"]) == int(video_resolution)
            ]

            if filtered_video_data:
                videoslist = filtered_video_data
            else:
                # No videos matched the specified resolution; use the highest resolution
                videoslist = [
                    max(
                        self.result.get('video'), key=lambda x: int(x["height"]))
                ]
        else:
            # Use the video with the highest resolution by default
            videoslist = [max(self.result.get('video'), key=lambda x: int(x["height"]))]

        # VIDEO QUALITY
        if video_quality:
            if video_quality == "HQ":
                selected_video = max(
                    videoslist, key=lambda x: int(x["bitrate"])
                )
                selected_video["quality"] = "HQ" if len(videoslist) > 1 else "NA"

            elif video_quality == "LQ":
                selected_video = min(
                    videoslist, key=lambda x: int(x["bitrate"])
                )
                selected_video["quality"] = "LQ" if len(videoslist) > 1 else "NA"
            else:
                selected_video = max(
                    videoslist, key=lambda x: int(x["bitrate"]))

                selected_video["quality"] = "HQ" if len(videoslist) > 1 else "NA"

        videoslist = selected_video

        # DEFAULT AUDIO SORT

        self.result.get('audio').sort(key=custom_sort)
        audioslist = self.result.get('audio')

        # AUDIO LANGUAGE

        if audio_languages:
            requested_languages = audio_languages.split("-")
            filtered_audio_data = [
                audio for audio in audioslist if audio["lang"] in requested_languages
            ]

            if filtered_audio_data:
                audioslist = filtered_audio_data


        # Group by language and find the one with the highest bandwidth for each language
        unique_lang_audios = {}

        for audio in audioslist:
            lang = audio["lang"]

            if lang not in unique_lang_audios or int(audio["bitrate"]) > int(
                unique_lang_audios[lang]["bitrate"]
            ):
                unique_lang_audios[lang] = audio

        audioslist = list(unique_lang_audios.values())

        # AUDIO QUALITY
        if audio_quality:
            audioslist = self.filter_audio_quality(audioslist, audio_quality)

        refined_result = {
            "video" : videoslist,
            "audio" : audioslist,
            "subtitle" : self.result.get('subtitle') if self.parse_subs is True else None
        }
        
        filename = Filename(refined_result, self.init_file_name, self.ott, self.custom_group_tag).generate_filename_v2()

        return refined_result, filename
    
