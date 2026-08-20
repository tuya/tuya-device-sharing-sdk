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
    return "".join(f"{byte:02x}" for byte in bytes_data)


def convert_value(s: str) -> str:
    s = s.lower()
    vo = DBV1CircuitParamsVO()
    if len(s) >= 34 and s.startswith("010f"):
        # 帧 V1（头 010f，17 字节）
        _parse_full(vo, s)
    elif len(s) >= 36 and s.startswith("020f"):
        # 帧 V2（头 020f，18 字节，末字节为符号位）
        _parse_full(vo, s)
        sign = hex2decimal(s[34:36])
        if sign & 0x1:
            vo.electricCurrent = -vo.electricCurrent
        if sign & 0x2:
            vo.power = -vo.power
        if sign & 0x4:
            vo.reactivePower = -vo.reactivePower
        if sign & 0x8:
            vo.powerFactor = -vo.powerFactor
    else:
        # 老帧（8 字节，无头，仅电压/电流/有功）
        vo.voltage = hex2decimal(s[0:4]) / 10.0
        vo.electricCurrent = hex2decimal(s[4:10]) / 1000.0
        vo.power = hex2decimal(s[10:16]) / 1000.0
    # 跳过 None：老帧仍只输出 3 字段，与升级前逐字节一致
    return json.dumps({k: v for k, v in vo.__dict__.items() if v is not None})


def _parse_full(vo: "DBV1CircuitParamsVO", s: str) -> None:
    vo.voltage = hex2decimal(s[4:8]) / 10.0
    vo.electricCurrent = hex2decimal(s[8:14]) / 1000.0
    vo.power = hex2decimal(s[14:20]) / 1000.0
    vo.reactivePower = hex2decimal(s[20:26]) / 1000.0
    vo.apparentPower = hex2decimal(s[26:32]) / 1000.0
    vo.powerFactor = hex2decimal(s[32:34]) / 100.0


def hex2decimal(hex_str: str) -> int:
    if not hex_str:
        return 0
    hex_str = hex_str.lstrip("0")
    if not hex_str:
        return 0
    return int(hex_str, 16)


class DBV1CircuitParamsVO:
    def __init__(
        self,
        voltage: Optional[float] = None,
        electric_current: Optional[float] = None,
        power: Optional[float] = None,
        reactive_power: Optional[float] = None,
        apparent_power: Optional[float] = None,
        power_factor: Optional[float] = None,
    ):
        self.voltage = voltage
        self.electricCurrent = electric_current
        self.power = power
        self.reactivePower = reactive_power
        self.apparentPower = apparent_power
        self.powerFactor = power_factor
