import json
from typing import List, Dict
import colorsys
from .. import strategy

@strategy.register("dj_v1_scene_alg")
def convert(dp_item: tuple, config_item: dict) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value


class DJHsvVO:
    def __init__(self, h: float = None, s: float = None, v: float = None):
        self.h = h
        self.s = s
        self.v = v

    def __repr__(self):
        return f"DJHsvVO(h={self.h}, s={self.s}, v={self.v})"

class DJV1SceneVO:
    def __init__(self, frequency: int = None, bright: int = None, temperature: int = None, hsv: List[DJHsvVO] = None):
        self.frequency = frequency
        self.bright = bright
        self.temperature = temperature
        self.hsv = hsv if hsv is not None else []

    def __repr__(self):
        return f"DJV1SceneVO(frequency={self.frequency}, bright={self.bright}, temperature={self.temperature}, hsv={self.hsv})"

def hex2decimal(hex_str: str) -> int:
    return int(hex_str, 16)

def split_str_by_width(s: str, width: int) -> List[str]:
    return [s[i:i+width] for i in range(0, len(s), width)]

def rgb2hsv_standard(r: int, g: int, b: int) -> Dict[str, float]:
    hsv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hsv_map = {"H": hsv[0], "S": hsv[1], "V": hsv[2]}
    return hsv_map

def scale_round(value: float, scale: int) -> float:
    return round(value, scale)

def convert_value(str_colour_value: str) -> str:
    if not str_colour_value:
        return ""

    vo = DJV1SceneVO()

    bright = hex2decimal(str_colour_value[0:2])
    temperature = hex2decimal(str_colour_value[2:4])
    frequency = hex2decimal(str_colour_value[4:6])
    hsv_len = hex2decimal(str_colour_value[6:8])

    vo.bright = bright
    vo.temperature = temperature
    vo.frequency = frequency

    hsv_str = str_colour_value[8:]
    rgb_str_list = split_str_by_width(hsv_str, 6)

    for rgb_str in rgb_str_list:
        r = hex2decimal(rgb_str[0:2])
        g = hex2decimal(rgb_str[2:4])
        b = hex2decimal(rgb_str[4:6])

        map = rgb2hsv_standard(r, g, b)

        h = scale_round(map["H"] * 360, 1)
        s = scale_round(map["S"] * 255, 1)
        v = scale_round(map["V"] * 255, 1)

        item_vo = DJHsvVO(h, s, v)

        vo.hsv.append(item_vo)

    return json.dumps(vo, default=lambda o: o.__dict__)