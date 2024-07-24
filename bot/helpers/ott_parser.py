import argparse
import sys, uuid
from io import StringIO
import shlex

parser_data = {
    "tplay": [
        {
            "short_parsername": "c",
            "long_parsername": "channel",
            "help": "Provide Channel same as in tplay.json kept in static folder",
            "example": "Nick JR",
            "required": None,
            "default": None,
        },
        {
            "short_parsername": "ss",
            "long_parsername": "start",
            "help": "The start time to DL for the catchup",
            "example": "27/07/2023+13:00:00",
            "required": None,
            "default": None,
        },
        {
            "short_parsername": "to",
            "long_parsername": "end",
            "help": "The end time to DL for the catchup",
            "example": "27/07/2023+13:30:00",
            "required": None,
            "default": None,
        },
        {
            "short_parsername": "title",
            "long_parsername": "title",
            "help": "The title to save the file name to",
            "example": "Hello World",
            "required": None,
            "default": "",
        },
        {
            "short_parsername": "r",
            "long_parsername": "resolution",
            "help": "DL Particular Resolution",
            "example": "1080p, 720p, 480p",
            "default": None,
            "required": None,
        },
        {
            "short_parsername": "info",
            "long_parsername": "info",
            "help": "Get Stream Info",
            "example": "Leave Blank",
            "default": False,
            "required": None,
        },
        {
            "short_parsername": "alang",
            "long_parsername": "alang",
            "example": "hi-ta-te",
            "help": "DL Particular Audios",
            "default": None,
            "required": None,
        },
        {
            "short_parsername": "vquality",
            "long_parsername": "vquality",
            "example": "HQ or LQ",
            "help": "DL HQ or LQ of a Particular Resolution",
            "default": "HQ",
            "required": None,
        },
        {
            "short_parsername": "aquality",
            "long_parsername": "aquality",
            "example": "HQ or LQ",
            "help": "DL HQ or LQ of a Particular Resolution",
            "default": None,
            "required": None,
        },
        {
            "short_parsername": "acodec",
            "long_parsername": "acodec",
            "example": "ddplus, dd+, dd, dolbydigial, aac",
            "help": "Audio Codec to be Downloaded can be mp4a.40.2 (AAC), ac-3 (DD), or ec-3(DD+)",
            "default": None,
            "required": None,
        }

    ]
}


def ott_argument_parser(args_string, ott):
    args_list = shlex.split(args_string)
    parser = argparse.ArgumentParser()
    for data in parser_data[ott]:
        parser.add_argument(
            f"--{data['long_parsername']}",
            f"-{data['short_parsername']}",
            help=data["help"],
            dest=data['long_parsername'],
            default=data["default"],
            required=data["required"],
            nargs='?' if data["long_parsername"] in ['hevc', 'info'] else None
        )

    # Create a string buffer to capture the error message
    error_buffer = StringIO()
    sys.stderr = error_buffer

    try:
        parsed_args = parser.parse_args(args_list)
    except SystemExit:
        error_message = error_buffer.getvalue().strip()
        print(error_message)
        raise Exception(error_message)

    sys.stderr = sys.__stderr__

    return parsed_args
