import json
from .. import strategy


@strategy.register("hb_range_v1")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, ""

    status_value = convert_value(int(dp_value))
    return status_key, status_value

import math

def convert_value(input, t_min = 0, t_max = 100, i_min = 25, i_max = 255, mark = False):
    input_num = input
    if input_num > i_max:
        input_num = i_max
    if input_num < i_min:
        input_num = i_min

    num = (((t_max - t_min) * 1.0) / ((i_max - i_min) * 1.0)) * (input_num - i_min) + (t_min * 1.0)

    target = 0
    if mark:
        target = math.ceil(num)
    else:
        target = math.floor(num)

    if target > t_max:
        target = t_max
    if target < t_min:
        target = t_min
    return target