import json

from .. import strategy
from .default import convert_value as convert_default_value


@strategy.register("enum")
def convert(dp_item: tuple, config_item: dict = None) -> tuple:
    """枚举策略转换规则

    根据 dp value 的值作为 key 从 enumMappingMap 中获取对应的 value 映射的标准指令值
    如果没有找到对应的 value 映射，则使用默认的转换规则
    :param dp_item: dp 值
    :param config_item: 转换规则
    :return: 标准指令值
    """
    dp_key, dp_value = dp_item
    status_key, _ = json.loads(config_item["statusFormat"]).popitem()
    enum_mappings = config_item["enumMappingMap"]
    status_value = None
    if str(dp_value) in enum_mappings and "value" in enum_mappings[str(dp_value)]:
        status_value = enum_mappings[str(dp_value)]["value"]
    if status_value is None:
        status_value = convert_default_value(config_item)
    return status_key, status_value




