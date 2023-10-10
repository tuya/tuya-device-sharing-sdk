import json
from typing import Optional

from .. import strategy


@strategy.register("dj_v2_music_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value

class DJV2MusicDataVO:
    def __init__(self):
        self.change_mode: Optional[str] = None
        self.h: Optional[int] = None
        self.s: Optional[int] = None
        self.v: Optional[int] = None
        self.bright: Optional[int] = None
        self.temperature: Optional[int] = None

    def __str__(self):
        return f"DJV2MusicDataVO{{changeMode='{self.change_mode}', h={self.h}, s={self.s}, v={self.v}, bright={self.bright}, temperature={self.temperature}}}"


def convert_value(str_: str) -> str:
    vo = DJV2MusicDataVO()
    if not str_:
        return ""

    flag = hex2decimal(str_[0:1])
    if flag == 0:
        vo.change_mode = "direct"
    if flag == 1:
        vo.change_mode = "gradient"

    vo.h = hex2decimal(str_[1:5])
    vo.s = hex2decimal(str_[5:9])
    vo.v = hex2decimal(str_[9:13])
    vo.bright = hex2decimal(str_[13:17])
    vo.temperature = hex2decimal(str_[17:])

    return json.dumps(vo.__dict__)


def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip('0')
    if not hex_str:
        return 0
    return int(hex_str, 16)




