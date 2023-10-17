from enum import Enum

from .custom_strategy import custom_convert


class Strategy(object):
    def __init__(self):
        self._strategies = {}

    def register(self, name):
        def decorator(func):
            self._strategies[name] = func
            return func
        return decorator

    def convert(self, name, *args, **kwargs):
        if name not in self._strategies:
            raise Exception("Strategy {} not found.".format(name))

        # 标准指令集脚本转换
        return self._strategies.get(name)(*args, **kwargs)
        # 定制逻辑转换
        # _, config_item = args
        # status_item = custom_convert(status_item, config_item)
        # return status_item

# singleton
strategy = Strategy()


# 策略转换结束后的定制逻辑
# 定义枚举
class CMDCCodeEnum(Enum):
    switch = 1
    switchOne = 2
    switchTwo = 3
    switchThree = 4
    switchUsbOne = 5
    # ... (以此类推)

# 定义类
class CMDCStatusVO:
    def __init__(self, cmdcCodeEnum, type):
        self.cmdcCodeEnum = cmdcCodeEnum
        self.type = type

# 初始化字典
status2CMDCCodeMap = {}

status2CMDCCodeMap["switch"] = CMDCStatusVO(CMDCCodeEnum.switch, 1)
status2CMDCCodeMap["switch_1"] = CMDCStatusVO(CMDCCodeEnum.switchOne, 1)
# ... (以此类推)



if __name__ == "__main__":
    @strategy.register("f1")
    def f1():
        print("f1")

    @strategy.register("f2")
    def f2():
        print("f2")

    strategy.convert("f1")
    strategy.convert("f2")
    strategy.convert("f")