import json
from typing import Dict, Optional
from colorsys import rgb_to_hsv
from .. import strategy


@strategy.register("dj_v1_hsv_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value


class DJHsvVO:
    def __init__(self, h: Optional[float] = None, s: Optional[float] = None, v: Optional[float] = None):
        self.h = h
        self.s = s
        self.v = v

    def __str__(self):
        return f"DJHsvVO{{h={self.h}, s={self.s}, v={self.v}}}"


class HSVColorVO:
    def __init__(self, hue: float, saturation: float, brightness: float):
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness


def hex2decimal(hex_str: str) -> int:
    if not hex_str or len(hex_str) > 2:
        return 0
    return int(hex_str, 16)


def rgb2hsv_standard(red: int, green: int, blue: int) -> Dict[str, float]:
    hsv = rgb_to_hsv(red / 255, green / 255, blue / 255)
    return {"H": hsv[0], "S": hsv[1], "V": hsv[2]}


def scale_round(e: float, scale: int) -> float:
    return round(e, scale)


def get_hsv_from_color_dp_value(dp_value: str) -> HSVColorVO:
    hh_hex = dp_value[6:8]
    hl_hex = dp_value[8:10]
    s_hex = dp_value[10:12]
    v_hex = dp_value[12:]

    hh_bin = format(int(hh_hex, 16), "b")
    hl_bin = format(int(hl_hex, 16), "b")

    hh_bin = add_zero(hh_bin, 8)
    hl_bin = add_zero(hl_bin, 8)

    h_string = hh_bin + hl_bin
    h = int(h_string, 2) / 1.0
    s = int(s_hex, 16) * 1.0 / 255
    v = int(v_hex, 16) * 1.0 / 255

    hsv_color_vo = HSVColorVO(h, round(s, 3), round(v, 3))
    return hsv_color_vo


def add_zero(s: str, length: int) -> str:
    while len(s) < length:
        s = "0" + s
    return s


def convert_value(str_colour_value: str) -> str:
    if str_colour_value[6:] == "0168ffff":
        r = hex2decimal(str_colour_value[0:2])
        g = hex2decimal(str_colour_value[2:4])
        b = hex2decimal(str_colour_value[4:6])

        hsv_map = rgb2hsv_standard(r, g, b)

        hsv_vo = DJHsvVO()
        hsv_vo.h = scale_round(hsv_map["H"] * 360.0, 1)
        hsv_vo.s = scale_round(hsv_map["S"] * 255.0, 1)
        hsv_vo.v = scale_round(hsv_map["V"] * 255.0, 1)

        return json.dumps(hsv_vo.__dict__)

    vo = get_hsv_from_color_dp_value(str_colour_value)

    hsv_vo = DJHsvVO()
    hsv_vo.h = vo.hue
    hsv_vo.s = scale_round(vo.saturation * 255.0, 1)
    hsv_vo.v = scale_round(vo.brightness * 255.0, 1)

    return json.dumps(hsv_vo.__dict__)