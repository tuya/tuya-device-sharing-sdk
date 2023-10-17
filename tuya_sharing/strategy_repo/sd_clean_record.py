import json
from .. import strategy


@strategy.register("sd_clean_record")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, dp_value

    status_value = convert_value(dp_value)
    return status_key, status_value


def convert_value(string_value):
    length = len(string_value)
    if length == 6:
        return clean_time_and_area_resolve(string_value)
    elif length == 11:
        return clean_time_and_area_with_map_resolve(string_value)
    elif length == 18:
        return recored_and_clean_time_with_area_resolve(string_value)
    else:
        return all_property_resolve(string_value)

def clean_time_and_area_resolve(value):
    clean_time = int(value[:3])
    clean_area = int(value[3:6])
    data = {"record_time": "", "clean_time": clean_time, "clean_area": clean_area, "map_id": ""}
    return json.dumps(data)

def recored_and_clean_time_with_area_resolve(value):
    record_time = value[:12]
    clean_time = int(value[12:15])
    clean_area = int(value[15:18])
    data = {"record_time": record_time, "clean_time": clean_time, "clean_area": clean_area, "map_id": ""}
    return json.dumps(data)

def clean_time_and_area_with_map_resolve(value):
    clean_time = int(value[:3])
    clean_area = int(value[3:6])
    map_id = value[6:11]
    data = {"record_time": "", "clean_time": clean_time, "clean_area": clean_area, "map_id": map_id}
    return json.dumps(data)

def all_property_resolve(value):
    record_time = value[:12]
    clean_time = int(value[12:15])
    clean_area = int(value[15:18])
    map_id = value[18:23]
    data = {"record_time": record_time, "clean_time": clean_time, "clean_area": clean_area, "map_id": map_id}
    return json.dumps(data)