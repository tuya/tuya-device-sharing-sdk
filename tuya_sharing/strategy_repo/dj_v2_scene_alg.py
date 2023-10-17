import json
from typing import List

from .. import strategy


@strategy.register("dj_v2_scene_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value

class DJV2SceneUnitVO:
    def __init__(self):
        self.unit_switch_duration = 0
        self.unit_gradient_duration = 0
        self.unit_change_mode = ""
        self.h = 0
        self.s = 0
        self.v = 0
        self.bright = 0
        self.temperature = 0

class DJV2SceneDataVO:
    def __init__(self):
        self.scene_num = 0
        self.scene_units = []

def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip("0")
    if not hex_str:
        return 0
    return int(hex_str, 16)

def convert_value(str: str) -> str:
    vo = DJV2SceneDataVO()
    vo.scene_num = 1 + hex2decimal(str[:2])
    scene_units = []
    unit_str = str[2:]
    num = len(unit_str) // 26
    for i in range(num):
        item = unit_str[i * 26:(i + 1) * 26]
        unit_vo = DJV2SceneUnitVO()
        unit_vo.unit_switch_duration = hex2decimal(item[:2])
        unit_vo.unit_gradient_duration = hex2decimal(item[2:4])
        flag = hex2decimal(item[4:6])
        if flag == 0:
            unit_vo.unit_change_mode = "static"
        elif flag == 1:
            unit_vo.unit_change_mode = "jump"
        elif flag == 2:
            unit_vo.unit_change_mode = "gradient"
        unit_vo.h = hex2decimal(item[6:10])
        unit_vo.s = hex2decimal(item[10:14])
        unit_vo.v = hex2decimal(item[14:18])
        unit_vo.bright = hex2decimal(item[18:22])
        unit_vo.temperature = hex2decimal(item[22:])
        scene_units.append(unit_vo)
    vo.scene_units = scene_units
    return json.dumps(vo.__dict__, default=lambda o: o.__dict__)




