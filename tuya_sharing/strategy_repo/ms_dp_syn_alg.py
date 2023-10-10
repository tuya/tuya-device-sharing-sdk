import base64
import json
from .. import strategy


@strategy.register("ms_dp_syn_alg")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value

def convert_value(input_str):
    res = set()
    if not input_str:
        return res
    try:
        data = input_str
        sync_byte = base64.b64decode(data)
        data_size = len(sync_byte)
        step = 2
        bit_size = 8
        index = 0
        while index < data_size:
            partion = (sync_byte[index] & 0b01111111) & 0xFF
            value = int(sync_byte[index + 1] & 0xFF)
            for i_bit in range(bit_size):
                if is_true(value, i_bit):
                    unlock_index = (partion - 1) * 8 + i_bit
                    res.add(unlock_index)
            index += step
    except Exception as e:
        print("MsAlg-门锁上报解析错误，上报数据协议非法. input_str=" + input_str)
        res = set()
    return res

def pow2(num):
    return int(2 ** num)

def is_true(number, position):
    decimal_value = pow2(position)
    return (decimal_value & number) == decimal_value