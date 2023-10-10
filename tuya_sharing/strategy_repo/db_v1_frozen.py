import json
import base64

from .. import strategy


@strategy.register("db_v1_frozen")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(decode4hex_str(dp_value))
    return status_key, status_value


def decode(input: str) -> bytes:
    return base64.b64decode(input)

def decode4hex_str(input: str) -> str:
    bytes_data = decode(input)
    return ''.join(f'{byte:02x}' for byte in bytes_data)

class DBV1FrozenTimeVO:
    def __init__(self, day=0, hour=0):
        self.day = day
        self.hour = hour

def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip("0")
    if not hex_str:
        return 0
    return int(hex_str, 16)

def convert_value(str: str) -> str:
    vo = DBV1FrozenTimeVO()
    vo.day = hex2decimal(str[:2])
    vo.hour = hex2decimal(str[2:4])
    return json.dumps(vo.__dict__)