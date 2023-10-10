"""device api."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Optional
import time

from .customerapi import CustomerApi
from .customerlogging import logger


class DeviceFunction(SimpleNamespace):
    """device's function.

    Attributes:
        code(str): function's code
        desc(str): function's description
        name(str): function's name
        type(str): function's type, which may be Boolean, Integer, Enum, Json
        values(dict): function's value range
    """

    code: str
    desc: str
    name: str
    type: str
    values: dict[str, Any]


class DeviceStatusRange(SimpleNamespace):
    """device's status range.

    Attributes:
        code(str): status's code
        type(str): status's type, which may be Boolean, Integer, Enum, Json
        values(dict): status's value range
    """

    code: str
    type: str
    values: str


class CustomerDevice(SimpleNamespace):
    """Customer Device.

    Attributes:
          id: Device id
          name: Device name
          local_key: Key
          category: Product category
          product_id: Product ID
          product_name: Product name
          sub: Determine whether it is a sub-device, true-> yes; false-> no
          uuid: The unique device identifier
          asset_id: asset id of the device
          online: Online status of the device
          icon: Device icon
          ip: Device IP
          time_zone: device time zone
          active_time: The last pairing time of the device
          create_time: The first network pairing time of the device
          update_time: The update time of device status

          status: Status set of the device
          function: Instruction set of the device
          status_range: Status value range set of the device
    """

    id: str
    name: str
    local_key: str
    category: str
    product_id: str
    product_name: str
    sub: bool
    uuid: str
    asset_id: str
    online: bool
    icon: str
    ip: str
    time_zone: str
    active_time: int
    create_time: int
    update_time: int
    set_up: Optional[bool] = False
    support_local: Optional[bool] = False
    local_strategy: dict[int, dict[str, Any]] = {}

    status: dict[str, Any] = {}
    function: dict[str, DeviceFunction] = {}
    status_range: dict[str, DeviceStatusRange] = {}

    def __eq__(self, other):
        """If devices are the same one."""
        return self.id == other.id


class DeviceRepository:
    def __init__(self, customer_api: CustomerApi):
        self.api = customer_api
        self.filter = Filter(10)

    def query_devices_by_home(self, home_id: str) -> list[CustomerDevice]:
        response = self.api.get(f"/v1.0/m/life/ha/home/devices", {"homeId": home_id})
        return self._query_devices(response)

    def query_devices_by_ids(self, ids: list) -> list[CustomerDevice]:
        response = self.api.get("/v1.0/m/life/ha/devices/detail", {"devIds": ",".join(ids)})
        return self._query_devices(response)

    def _query_devices(self, response) -> list[CustomerDevice]:
        _devices = []
        if response["success"]:
            for item in response["result"]:
                device = CustomerDevice(**item)
                status = {}
                for item_status in device.status:
                    if "code" in item_status and "value" in item_status:
                        code = item_status["code"]
                        value = item_status["value"]
                        status[code] = value
                device.status = status
                self.update_device_specification(device)
                self.update_device_strategy_info(device)
                _devices.append(device)
        return _devices

    def update_device_specification(self, device: CustomerDevice):
        device_id = device.id
        response = self.api.get(f"/v1.1/m/life/{device_id}/specifications")
        if response.get("success"):
            result = response.get("result", {})
            function_map = {}
            for function in result["functions"]:
                code = function["code"]
                function_map[code] = DeviceFunction(**function)

            status_range = {}
            for status in result["status"]:
                code = status["code"]
                status_range[code] = DeviceStatusRange(**status)

            device.function = function_map
            device.status_range = status_range

    def update_device_strategy_info(self, device: CustomerDevice):
        device_id = device.id
        response = self.api.get(f"/v1.0/m/life/devices/{device_id}/status")
        support_local = True
        if response.get("success"):
            result = response.get("result", {})
            pid = result["productKey"]
            dp_id_map = {}
            for dp_status_relation in result["dpStatusRelationDTOS"]:
                if not dp_status_relation["supportLocal"]:
                    support_local = False
                    break
                # statusFormat valueDesc、valueType,enumMappingMap,pid
                dp_id_map[dp_status_relation["dpId"]] = {
                    "value_convert": dp_status_relation["valueConvert"],
                    "status_code": dp_status_relation["statusCode"],
                    "config_item": {
                        "statusFormat": dp_status_relation["statusFormat"],
                        "valueDesc": dp_status_relation["valueDesc"],
                        "valueType": dp_status_relation["valueType"],
                        "enumMappingMap": dp_status_relation["enumMappingMap"],
                        "pid": pid,
                    }
                }
            device.support_local = support_local
            if support_local:
                device.local_strategy = dp_id_map

            logger.debug(
                f"device status strategy dev_id = {device_id} support_local = {support_local} local_strategy = {dp_id_map}")

    def send_commands(self, device_id: str, commands: list[dict[str, Any]]):
        if self.filter.call(device_id, commands):
            self.api.post(f"/v1.1/m/thing/{device_id}/commands", None, {"commands": commands})


class Filter:
    def __init__(self, time: int):
        self.last_call_time = {}
        self.time_limit = time
        self.last_clean_time = 0

    def clean_expired_keys(self):
        current_time = time.time()
        if current_time - self.last_clean_time >= 10:
            expired_keys = [key for key, (_, last_time) in self.last_call_time.items() if
                            current_time - last_time >= 10]
            for key in expired_keys:
                del self.last_call_time[key]
            self.last_clean_time = current_time

    def call(self, dev_id, param) -> bool:
        self.clean_expired_keys()

        current_time = time.time()
        if dev_id in self.last_call_time:
            last_param, last_time = self.last_call_time[dev_id]
            if param != last_param or current_time - last_time >= self.time_limit:
                self.last_call_time[dev_id] = (param, current_time)
                logger.debug(f"filter receive one dev_id = {dev_id} param = {param}")
                return True
            else:
                logger.debug(f"filter receive two dev_id = {dev_id} param = {param}")
                return False
        else:
            self.last_call_time[dev_id] = (param, current_time)
            logger.debug(f"filter receive three dev_id = {dev_id} param = {param}")
            return True
