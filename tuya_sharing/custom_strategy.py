import json
from enum import Enum

class CMDCCodeEnum(Enum):
    switch = 1
    switchOne = 2
    switchTwo = 3
    switchThree = 4
    switchUsbOne = 5
    switchUsbTwo = 6
    switchUsbThree = 7
    switchLed = 9
    switchSound = 10
    switchSpray = 11
    countDown = 13
    change_mode = 14
    color = 15
    brightness = 17
    temp = 18
    mode = 19
    ledMode = 20
    lowOil = 21

class CMDCStatusVO:
    def __init__(self, cmdcCodeEnum, type):
        self.cmdcCodeEnum = cmdcCodeEnum
        self.type = type

status2CMDCCodeMap = {
    "switch": CMDCStatusVO(CMDCCodeEnum.switch, 1),
    "switch_1": CMDCStatusVO(CMDCCodeEnum.switchOne, 1),
    "switch_2": CMDCStatusVO(CMDCCodeEnum.switchTwo, 1),
    "switch_3": CMDCStatusVO(CMDCCodeEnum.switchThree, 1),
    "switch_usb1": CMDCStatusVO(CMDCCodeEnum.switchUsbOne, 1),
    "switch_usb2": CMDCStatusVO(CMDCCodeEnum.switchUsbTwo, 1),
    "switch_usb3": CMDCStatusVO(CMDCCodeEnum.switchUsbThree, 1),
    "switch_led": CMDCStatusVO(CMDCCodeEnum.switch, 1),
    "colour_data": CMDCStatusVO(CMDCCodeEnum.color, 4),
    "colour_data_v2": CMDCStatusVO(CMDCCodeEnum.color, 4),
    "bright_value": CMDCStatusVO(CMDCCodeEnum.brightness, 3),
    "bright_value_v2": CMDCStatusVO(CMDCCodeEnum.brightness, 3),
    "temp_value": CMDCStatusVO(CMDCCodeEnum.temp, 3),
    "temp_value_v2": CMDCStatusVO(CMDCCodeEnum.temp, 3),
    "switch_spray": CMDCStatusVO(CMDCCodeEnum.switchSpray, 1),
    "mode": CMDCStatusVO(CMDCCodeEnum.mode, 2),
    "countdown": CMDCStatusVO(CMDCCodeEnum.countDown, 3),
    "moodlighting": CMDCStatusVO(CMDCCodeEnum.ledMode, 2),
    "switch_sound": CMDCStatusVO(CMDCCodeEnum.switchSound, 1)
}


def custom_convert(status_item, config_item):
    status_code, status_value = status_item
    if status_code not in status2CMDCCodeMap:
        return status_item

    cmdc_status_vo = status2CMDCCodeMap.get(status_code)
    status_code = cmdc_status_vo.cmdcCodeEnum.name
    if cmdc_status_vo.type == 1: # Boolean 类型
        if status_code == "switch_1" and config_item["pid"] == "of3pvbtfmg5jdw7o":
            status_code = CMDCCodeEnum.switch.name
            status_value = 1 if status_value == True or status_value == "true" or status_value == 1 else 0
    elif cmdc_status_vo.type == 2: # Enum 类型
        if status_code == "moodlighting":
            if is_integer(str(status_value)):
                status_value = int(status_value)
            else:
                return status_item
        elif status_code == "mode":
            if str(status_value) == "large":
                status_value = 2
            elif str(status_value) == "middle":
                status_value = 1
            elif str(status_value) == "small":
                status_value = 0
            elif str(status_value) == "interval":
                status_value = 3
            elif str(status_value) == "continuous":
                status_value = 4
            else:
                return status_item
        else:
            return status_item
    elif cmdc_status_vo.type == 3: # 数值类型
        if status_code == "bright_value":
            status_value = get_common_brightness_value(status_value, 25, 255)
        elif status_code == "bright_value_v2":
            status_value = get_common_brightness_value(status_value, 10, 1000)
        elif status_code == "temp_value":
            if is_integer(str(status_value)):
                status_value = int(status_value) * 100 / 255
            else:
                return status_item
        elif status_code == "temp_value_v2":
            if is_integer(str(status_value)):
                status_value = int(status_value) / 10
            else:
                return status_item
        elif status_code == "countdown":
            if str(status_value) == "cancel":
                status_value = 0
            elif is_integer(str(status_value)):
                status_value = str(int(status_value) * 60)
            else:
                return status_item
        else:
            return status_item
    elif cmdc_status_vo.type == 4: # 特殊类型
        if status_code == "colour_data" or status_code == "colour_data_v2":
            if status_value is None:
                return status_item
            else:
                if status_code == "colour_data" or status_code == "colour_data_v2":
                    skill_vo = get_skill_vo(config_item["pid"], status_item)
                    status_value = skill_vo.value
                    my_json = json.loads(str(status_value))
                    v = int(my_json["v"])
                    if status_code == "colour_data":
                        status_value = (v * 100 / 255) if (v * 100 % 255 == 0) else (v * 100 / 255 + 1)
                    else:
                        status_value = v / 10
                else:
                    pass
        else:
            return status_item
    return status_code, status_value


def get_common_brightness_value(value, min, max):
    try:
        temp_value = int(value)
    except ValueError:
        return None

    if temp_value == max:
        return 100
    elif temp_value == min:
        return min
    else:
        return (temp_value - 25) * 100 / 255


def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class SkillCodeEnum(Enum):
    Color = {"type": "Enum", "desc": "颜色", "descEn": "Color"}


class SkillItemVO:
    def __init__(self, skill=None, value=None):
        self.skill = skill
        self.value = value


class SkillCodeVO:
    def __init__(self, skillCodeEnum=None, name=None, type=None, desc=None, descEn=None):
        if skillCodeEnum:
            self.name = skillCodeEnum.name
            self.type = None # Replace with appropriate conversion method for ValueType
            self.desc = skillCodeEnum.value["desc"]
            self.descEn = skillCodeEnum.value["descEn"]
        if name and type and desc and descEn:
            self.name = name
            self.type = type
            self.desc = desc
            self.descEn = descEn


def get_skill_item_vo(skill, value):
    return SkillItemVO(skill.name, value)


def get_skill_vo(pid, status_dto):
    status_code, status_value = status_dto
    if status_value is None:
        return None
    if str(status_value).startswith("{"):
        try:
            jsonObject = json.loads(str(status_value))
            h = jsonObject["h"]
            s = jsonObject["s"]
            v = jsonObject["v"]
            if ((s < 30 and 221 <= v <= 255) and status_code == 'colour_data') or \
                ((s < 227 and 866 <= v <= 1000) and status_code == 'colour_data_v2') or \
                ((s < 60 and 221 <= v <= 255) and status_code == 'colour_data_hsv'):
                return get_skill_item_vo(SkillCodeVO(SkillCodeEnum.Color), "white")
            else:
                if   0 <= h <= 5 or 358 <= h <= 360: color = "red"
                elif 6 <= h <= 16: color = "orange"
                elif 17 <= h <= 26: color = "yellow"
                elif 27 <= h <= 32: color = "golden"
                elif 33 <= h <= 68: color = "yellow"
                elif 69 <= h <= 133: color = "green"
                elif 134 <= h <= 208: color = "cyan"
                elif 209 <= h <= 260: color = "blue"
                elif 261 <= h <= 316: color = "purple"
                elif 317 <= h <= 357: color = "pink"
                else: return None
                return get_skill_item_vo(SkillCodeVO(SkillCodeEnum.Color), color)
        except Exception as e:
            print("Color e: ", e, ", pid: ", pid, ", value: ", status_value) # Replace with your logging mechanism
    elif is_integer(str(status_value)):
        num = int(status_value)
        if   0 <= num <= 3: color = "red"
        elif 4 <= num <= 6: color = "orange"
        elif 7 <= num <= 27: color = "pink"
        elif 28 <= num <= 60: color = "purple"
        elif 61 <= num <= 80: color = "blue"
        elif 81 <= num <= 125: color = "cyan"
        elif 126 <= num <= 233: color = "green"
        elif 234 <= num <= 249: color = "yellow"
        elif 250 <= num <= 255: color = "golden"
        else: return None
        return get_skill_item_vo(SkillCodeVO(SkillCodeEnum.Color), color)
    return get_skill_item_vo(SkillCodeVO(SkillCodeEnum.Color), status_value)