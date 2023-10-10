import base64
import json

from .. import strategy


@strategy.register("db_v1_daily")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(decode4_to_hex_str(dp_value))
    return status_key, status_value


class DBV1DailyElectricDataVO:
    def __init__(self):
        self.startMonth = 0
        self.startDay = 0
        self.endMonth = 0
        self.endDay = 0
        self.electricTotal = 0.0

    def to_json(self):
        return json.dumps(self.__dict__)

def convert_value(data_str):
    vo = DBV1DailyElectricDataVO()
    vo.startMonth = hex_to_decimal(data_str[0:2])
    vo.startDay = hex_to_decimal(data_str[2:4])
    vo.endMonth = hex_to_decimal(data_str[4:6])
    vo.endDay = hex_to_decimal(data_str[6:8])
    vo.electricTotal = hex_to_decimal(data_str[8:16]) / 100.0
    return vo.to_json()

def decode(input_str):
    return base64.b64decode(input_str)

def decode4_to_hex_str(input_str):
    bytes_data = decode(input_str)
    return ''.join('{:02x}'.format(x) for x in bytes_data)

def hex_to_decimal(hex_str):
    hex_str = hex_str.lstrip('0')
    return int(hex_str or "0", 16)