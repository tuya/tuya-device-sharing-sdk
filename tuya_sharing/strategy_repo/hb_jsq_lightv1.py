import json
from .. import strategy


@strategy.register("hb_jsq_lightv1")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    if dp_value is None:
        return status_key, ""
    else:
        return status_key, dp_value + "|0|0"
