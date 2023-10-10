import json
import colorsys
from .. import strategy


@strategy.register("hb_djv1_color")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value


def convert_value(json_str):
    h, s, v = colorStrToHsvVOJson(json_str)
    rgb_map = hsv2rgbDecimalStandard(h, s, v)
    r = rgb_map["R"]
    g = rgb_map["G"]
    b = rgb_map["B"]
    return "|".join(map(str, [r, g, b]))


def colorStrToHsvVOJson(color_str):
    color_dict = json.loads(color_str)
    h = float(color_dict["h"]) / 360
    s = float(color_dict["s"]) / 255
    v = float(color_dict["v"]) / 255
    return h, s, v


def hsv2rgbDecimalStandard(h, s, v):
    rgb = colorsys.hsv_to_rgb(h, s, v)
    rgb_map = {
        "R": int(rgb[0] * 255),
        "G": int(rgb[1] * 255),
        "B": int(rgb[2] * 255),
    }
    return rgb_map