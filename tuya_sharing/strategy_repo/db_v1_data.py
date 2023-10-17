import base64
import json
import re
from collections import namedtuple

from .. import strategy


@strategy.register("db_v1_data")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(decode(dp_value))
    return status_key, status_value


def decode(input_str):
    return base64.b64decode(input_str)

DBV1PowerAndTimeVO = namedtuple('DBV1PowerAndTimeVO', ['power', 'year', 'month', 'date', 'hour', 'minute', 'second'])

def convert_value(str_input):
    res = DBV1PowerAndTimeVO(
        power = hex2dec(str_input[:8]) / 100.0,
        year = hex2dec(str_input[8:10]),
        month = hex2dec(str_input[10:12]),
        date = hex2dec(str_input[12:14]),
        hour = hex2dec(str_input[14:16]),
        minute = hex2dec(str_input[16:18]),
        second = hex2dec(str_input[18:20])
    )
    return json.dumps(res._asdict())

def average_str(input_string, length):
    if length < 0:
        return None
    res = []
    str_len = len(input_string)
    cur = 0
    while cur <= str_len:
        if cur + length > str_len:
            cur += length
            continue
        str_val = input_string[cur:cur+length]
        res.append(str_val)
        cur += length
    return res


def hex2dec(hex_str):
    if not hex_str:
        return 0
    hex_input = re.sub('^0+', '', hex_str)
    if not hex_input:
        return 0
    return int(hex_input, 16)