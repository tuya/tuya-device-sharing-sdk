import json
import base64

from .. import strategy


@strategy.register("cz_timer1_alg")
def convert(dp_item: tuple, config_item: dict) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(numDecodeToIntList(dp_value))
    return status_key, status_value


def numDecodeToIntList(input):
    bytes = base64.b64decode(input)
    return [item & 0xFF for item in bytes]

def convert_value(input, mark = False):
    vos = []
    if mark:
        for i in range(0, len(input), 10):
            tempVO = {}
            tempVO["timer_switch"] = integer2bool(input[i])
            tempVO["week_day"] = int2weekArr2(input[i + 1])
            tempVO["start_time"] = intArr2Str(input[i + 2], input[i + 3])
            tempVO["end_time"] = intArr2Str(input[i + 4], input[i + 5])
            tempVO["open_time"] = intArr2Str(input[i + 6], input[i + 7])
            tempVO["close_time"] = intArr2Str(input[i + 8], input[i + 9])
            vos.append(tempVO)
    else:
        for i in range(0, len(input), 6):
            tempVO = {}
            tempVO["timer_switch"] = integer2bool(input[i])
            tempVO["week_day"] = int2weekArr2(input[i + 1])
            tempVO["start_time"] = intArr2Str(input[i + 2], input[i + 3])
            tempVO["end_time"] = intArr2Str(input[i + 4], input[i + 5])
            vos.append(tempVO)
    return json.dumps(vos)

def integer2bool(integer):
    return integer > 0

def int2weekArr2(input):
    binary_str = format(input, 'b')[::-1]
    week_days = [i for i, bit in enumerate(binary_str) if bit == '1']
    return week_days

def intArr2Str(high, low):
    res_int = high * 256 + low
    hour = str(res_int // 60).zfill(2)
    minute = str(res_int % 60).zfill(2)
    return f"{hour}:{minute}"
