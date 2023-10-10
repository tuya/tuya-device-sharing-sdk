import json
from .. import strategy


@strategy.register("default")
def convert(dp_item: tuple, config_item: dict) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is not None and dp_value != "":
        return status_key, dp_value

    status_value = convert_value(config_item)
    return status_key, status_value


def convert_value(config_item):
    value_type = config_item["valueType"].capitalize()
    if value_type == "Boolean":
        status_value = False
    elif value_type == "Integer":
        status_value = json.loads(config_item["valueDesc"]).get("min")
    elif value_type == "Enum":
        status_value = json.loads(config_item["valueDesc"]).get("range")[0]
    elif value_type in ["String", "Raw", "Bitmap"]:
        status_value = ""
    else:
        status_value = ""
    return status_value
