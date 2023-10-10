import base64
import json
import math
from enum import Enum

from .. import strategy


@strategy.register("db_v1_alarm")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(decode4HexStr(dp_value))
    return status_key, status_value


def decode(input):
    return base64.b64decode(input)


def decode4HexStr(input):
    bytes = decode(input)
    return ''.join(format(x, '02x') for x in bytes)


def averageStr(inputString, length):
    if length < 0:
        return None

    return [inputString[i:i + length] for i in range(0, len(inputString), length)]


def hex2Decimal(hex):
    if not hex:
        return 0

    hex = hex.lstrip('0')
    return int(hex, 16) if hex else 0


class DBV1AlarmSetElectricEnum(Enum):
    OVERCURRENT = (1, "overcurrent", 0)
    THREE_PHASE_CURRENT_IMBALANCE = (2, "three_phase_current_imbalance", 0)
    AMMETER_OVERVOLTAGE = (3, "ammeter_overvoltage", 0)
    UNDER_VOLTAGE = (4, "under_voltage", 0)
    TREE_PHASE_CURRENT_LOSS = (5, "three_phase_current_loss", None)
    POWER_FAILURE = (6, "power_failure", None)
    MAGNETIC = (7, "magnetic", None)
    INSUFFICIENT_BALANCE = (8, "insufficient_balance", 0)
    ARREARS = (9, "arrears", None)
    BATTERY_OVERVOLTAGE = (10, "battery_overvoltage", 2)
    COVER_OPEN = (11, "cover_open", None)
    METER_COVER_OPEN = (12, "meter_cover_open", None)
    FAULT = (13, "fault", None)

    @staticmethod
    def getById(id):
        for alarmEnum in DBV1AlarmSetElectricEnum:
            if alarmEnum.value[0] == id:
                return alarmEnum
        return None


def convert_value(param):
    list = []
    stringList = averageStr(param, 8)
    for string in stringList:
        vo = {}
        alarmId = hex2Decimal(string[0:2])
        byId = DBV1AlarmSetElectricEnum.getById(alarmId)
        if byId is None:
            continue
        vo['alarmCode'] = byId.value[1]
        vo['doAction'] = hex2Decimal(string[2:4]) == 1
        if byId.value[2] is not None:
            threshold = hex2Decimal(string[4:8]) / math.pow(10, byId.value[2])
            if byId.value[2] > 0:
                vo['threshold'] = str(threshold)
            else:
                vo['threshold'] = str(int(threshold))
        list.append(vo)
    return json.dumps(list)