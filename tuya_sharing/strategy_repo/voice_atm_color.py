import colorsys
import json

from .. import strategy


@strategy.register("voice_atm_color")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value

class DJHsvVO:
    def __init__(self, h=0, s=0, v=0):
        self.h = h
        self.s = s
        self.v = v

    def __str__(self):
        return f"DJHsvVO{{h={self.h}, s={self.s}, v={self.v}}}"

class HSVColorVO:
    def __init__(self, hue=0, saturation=0, brightness=0):
        self.hue = hue
        self.saturation = saturation
        self.brightness = brightness

def add_zero(s, length):
    while len(s) < length:
        s = "0" + s
    return s

def convert_value(str_colour_value):
    if str_colour_value[6:] == "0168ffff":
        r_s = str_colour_value[0:2]
        r_g = str_colour_value[2:4]
        r_b = str_colour_value[4:6]

        r = int(r_s, 16)
        g = int(r_g, 16)
        b = int(r_b, 16)

        hsv_map = rgb2hsv_standard(r, g, b)

        hsv_vo = DJHsvVO(
            h=round(hsv_map["H"] * 360, 1),
            s=round(hsv_map["S"] * 255, 1),
            v=round(hsv_map["V"] * 255, 1)
        )

        return json.dumps(hsv_vo.__dict__)

    vo = get_hsv_from_color_dp_value(str_colour_value)

    hsv_vo = DJHsvVO(
        h=vo.hue,
        s=round(vo.saturation * 255, 1),
        v=round(vo.brightness * 255, 1)
    )

    return json.dumps(hsv_vo.__dict__)

def rgb2hsv_standard(red, green, blue):
    hsv = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    return {"H": hsv[0], "S": hsv[1], "V": hsv[2]}

def get_hsv_from_color_dp_value(dp_value):
    hh_hex = dp_value[6:8]
    hl_hex = dp_value[8:10]

    s_hex = dp_value[10:12]
    v_hex = dp_value[12:]

    hh_bin = add_zero(format(int(hh_hex, 16), "b"), 8)
    hl_bin = add_zero(format(int(hl_hex, 16), "b"), 8)

    h_string = hh_bin + hl_bin
    h = int(h_string, 2) / 1.0
    s = int(s_hex, 16) / 255
    v = int(v_hex, 16) / 255

    hsv_color_vo = HSVColorVO(
        hue=h,
        saturation=round(s, 4),
        brightness=round(v, 4)
    )

    return hsv_color_vo