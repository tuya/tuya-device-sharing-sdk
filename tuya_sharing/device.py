"""device api."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from .customerapi import CustomerApi


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

    status: dict[str, Any] = {}
    function: dict[str, DeviceFunction] = {}
    status_range: dict[str, DeviceStatusRange] = {}

    def __eq__(self, other):
        """If devices are the same one."""
        return self.id == other.id


class DeviceRepository:
    def __init__(self, customer_api: CustomerApi):
        self.api = customer_api

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

    def send_commands(self, device_id: str, commands: list[dict[str, Any]]):
        self.api.post(f"/v1.1/m/thing/{device_id}/commands", None, {"commands": commands})
