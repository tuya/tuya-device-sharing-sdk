import json
from typing import Optional

from .. import strategy


@strategy.register("dj_v2_color_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value


class DJV2ColourDataVO:
    def __init__(self, h: Optional[int] = None, s: Optional[int] = None, v: Optional[int] = None):
        self.h = h
        self.s = s
        self.v = v

    def __str__(self):
        return f"DJV2ColourDataVO{{h={self.h}, s={self.s}, v={self.v}}}"


def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0

    hex_str = hex_str.lstrip("0")

    if not hex_str:
        return 0

    return int(hex_str, 16)


def convert_value(str_input: str) -> str:
    vo = DJV2ColourDataVO()
    vo.h = hex2decimal(str_input[0:4])
    vo.s = hex2decimal(str_input[4:8])
    vo.v = hex2decimal(str_input[8:12])
    return json.dumps(vo.__dict__)
