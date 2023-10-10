from base64 import b64decode
import json
import re

from .. import strategy


@strategy.register("db_v1_tariff")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(decode(dp_value))
    return status_key, status_value



class TimerVO:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


class DBV1TariffPeriodBO:
    def __init__(self):
        self.monday = []
        self.tuesday = []
        self.wednesday = []
        self.thursday = []
        self.friday = []
        self.saturday = []
        self.sunday = []


def decode(input_string):
    return b64decode(input_string)


def convert_value(str_input):
    datelist = average_str(str_input, 12)
    if len(datelist) != 7:
        return ""
    dbv1_tariff_period = DBV1TariffPeriodBO()

    for i in range(7):
        timer_list = []
        item = datelist[i]
        if item != "0000000000000000":
            day_list = average_str(item, 4)
            for day_item in day_list:
                start_time = str(hex2decimal(day_item[:2]))
                end_time = str(hex2decimal(day_item[2:4]))
                timer_list.append(TimerVO(start_time, end_time))

        if i == 0:
            dbv1_tariff_period.monday = timer_list
        elif i == 1:
            dbv1_tariff_period.tuesday = timer_list
        elif i == 2:
            dbv1_tariff_period.wednesday = timer_list
        elif i == 3:
            dbv1_tariff_period.thursday = timer_list
        elif i == 4:
            dbv1_tariff_period.friday = timer_list
        elif i == 5:
            dbv1_tariff_period.saturday = timer_list
        elif i == 6:
            dbv1_tariff_period.sunday = timer_list

    return json.dumps(dbv1_tariff_period.__dict__, default=lambda o: o.__dict__)


def average_str(input_string, string_length):
    result = []
    if string_length < 0:
        return result
    input_len = len(input_string)
    for i in range(0, input_len, string_length):
        chunk = input_string[i:i+string_length]
        result.append(chunk)
    return result


def hex2decimal(hexinput):
    if not hexinput:
        return 0
    hexinput = re.sub("^0+", "", hexinput)
    if not hexinput:
        return 0
    return int(hexinput, 16)