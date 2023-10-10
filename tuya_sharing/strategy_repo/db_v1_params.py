import base64
import json
from typing import Optional

from .. import strategy


@strategy.register("db_v1_params")
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


def convert_value(s: str) -> str:
    vo = DBV1CircuitParamsVO()
    vo.voltage = hex2decimal(s[0:4]) / 10.0
    vo.electricCurrent = hex2decimal(s[4:10]) / 1000.0
    vo.power = hex2decimal(s[10:16]) / 1000.0
    return json.dumps(vo.__dict__)


def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip('0')
    if not hex_str:
        return 0
    return int(hex_str, 16)


class DBV1CircuitParamsVO:
    def __init__(self, voltage: Optional[float] = None, electric_current: Optional[float] = None,
                 power: Optional[float] = None):
        self.voltage = voltage
        self.electricCurrent = electric_current
        self.power = power