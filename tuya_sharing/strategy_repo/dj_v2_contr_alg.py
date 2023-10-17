import json

from .. import strategy


@strategy.register("dj_v2_contr_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value

class DJV2ControlDataVO:
    def __init__(self):
        self.change_mode = ""
        self.h = 0
        self.s = 0
        self.v = 0
        self.bright = 0
        self.temperature = 0


def convert_value(input_str):
    vo = DJV2ControlDataVO()
    if not input_str:
        return ""
    flag = hex2decimal(input_str[:1])
    if flag == 0:
        vo.change_mode = "direct"
    if flag == 1:
        vo.change_mode = "gradient"
    vo.h = hex2decimal(input_str[1:5])
    vo.s = hex2decimal(input_str[5:9])
    vo.v = hex2decimal(input_str[9:13])
    vo.bright = hex2decimal(input_str[13:17])
    vo.temperature = hex2decimal(input_str[17:])
    return json.dumps(vo.__dict__)


def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip("0")
    if not hex_str:
        return 0
    return int(hex_str, 16)




