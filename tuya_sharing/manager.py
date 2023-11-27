from __future__ import annotations

from typing import Any, Literal, Optional

from .customerapi import CustomerApi, CustomerTokenInfo, SharingTokenListener
from .device import DeviceRepository, CustomerDevice
from .home import HomeRepository, SmartLifeHome
from .scenes import SceneRepository
from .user import UserRepository
from .strategy import strategy

from abc import ABCMeta, abstractclassmethod
from .customerlogging import logger
from .mq import SharingMQ
import time

PROTOCOL_DEVICE_REPORT = 4
PROTOCOL_OTHER = 20
BIZCODE_ONLINE = "online"
BIZCODE_OFFLINE = "offline"
BIZCODE_NAME_UPDATE = "nameUpdate"
BIZCODE_DPNAME_UPDATE = "dpNameUpdate"
BIZCODE_BIND_USER = "bindUser"
BIZCODE_DELETE = "delete"


class Manager:

    def __init__(
            self,
            client_id: str,
            user_code: str,
            terminal_id: str,
            end_point: str,
            token_response: dict[str, Any] = None,
            listener: SharingTokenListener = None,
    ) -> None:
        self.terminal_id = terminal_id
        self.customer_api = CustomerApi(
            CustomerTokenInfo(token_response),
            client_id,
            user_code,
            end_point,
            listener,
        )
        self.device_map: dict[str, CustomerDevice] = {}
        self.user_homes: list[SmartLifeHome] = []
        self.home_repository = HomeRepository(self.customer_api)
        self.device_repository = DeviceRepository(self.customer_api)
        self.device_listeners = set()

        self.mq = None
        self.scene_repository = SceneRepository(self.customer_api)
        self.user_repository = UserRepository(self.customer_api)

    def update_device_cache(self):
        self.device_map.clear()
        homes = self.home_repository.query_homes()
        self.user_homes = homes

        for home in homes:
            devices_by_home = self.device_repository.query_devices_by_home(home.id)
            for device in devices_by_home:
                self.device_map[device.id] = device

    def report_version(self, ha_version: str, integration_version: str, sdk_version: str):
        logger.debug(
            f"report version ha_version={ha_version},integration_version={integration_version},sdk_version={sdk_version}")
        self.user_repository.user_version_report(ha_version, integration_version, sdk_version)

    def _update_device_list_info_cache(self, ids: list[str]):
        devices = self.device_repository.query_devices_by_ids(ids)
        for device in devices:
            self.device_map[device.id] = device

    def refresh_mq(self):
        if self.mq is not None:
            self.mq.stop()
            self.mq = None

        home_ids = [home.id for home in self.user_homes]
        device = [device for device in self.device_map.values() if
                  hasattr(device, "id") and getattr(device, "set_up", False)]

        sharing_mq = SharingMQ(self.customer_api, home_ids, device)
        sharing_mq.start()
        sharing_mq.add_message_listener(self.on_message)
        self.mq = sharing_mq

    def send_commands(
            self, device_id: str, commands: list[dict[str, Any]]
    ):
        return self.device_repository.send_commands(device_id, commands)

    def get_device_stream_allocate(
            self, device_id: str, stream_type: Literal["flv", "hls", "rtmp", "rtsp"]
    ) -> Optional[str]:
        """Get the live streaming address by device ID and the video type.

        These live streaming video protocol types are available: RTSP, HLS, FLV, and RTMP.

        Args:
          device_id(str): device id
          stream_type(str): type of stream

        Returns:
            None or URL to the requested stream
        """
        response = self.customer_api.post(f"/v1.0/m/ipc/{device_id}/stream/actions/allocate", None,
                                          {"type": stream_type})
        if response["success"]:
            return response["result"]["url"]
        return None

    def query_scenes(self) -> list:
        """Query home scenes."""
        home_ids = [home.id for home in self.user_homes]
        return self.scene_repository.query_scenes(home_ids)

    def trigger_scene(self, home_id: str, scene_id: str):
        """Trigger home scene"""
        self.scene_repository.trigger_scene(home_id, scene_id)

    def on_message(self, msg: dict):
        logger.debug(f"mq receive-> {msg}")

        try:
            protocol = msg.get("protocol", 0)
            data = msg.get("data", {})

            if protocol == PROTOCOL_DEVICE_REPORT:
                self._on_device_report(data["devId"], data["status"])
            if protocol == PROTOCOL_OTHER and data['bizCode'] in [BIZCODE_DELETE, BIZCODE_BIND_USER,
                                                                  BIZCODE_DPNAME_UPDATE, BIZCODE_NAME_UPDATE,
                                                                  BIZCODE_OFFLINE, BIZCODE_ONLINE]:
                self._on_device_other(data["bizData"]["devId"], data["bizCode"], data)
        except Exception as e:
            logger.error("on message error = %s", e)

    def __update_device(self, device: CustomerDevice):
        for listener in self.device_listeners:
            listener.update_device(device)

    def _on_device_report(self, device_id: str, status: list):
        device = self.device_map.get(device_id, None)
        if not device:
            return
        logger.debug(f"mq _on_device_report-> {status}")
        if device.support_local:
            for item in status:
                if "dpId" in item and "value" in item:
                    dp_id_item = device.local_strategy[item["dpId"]]
                    strategy_name = dp_id_item["value_convert"]
                    config_item = dp_id_item["config_item"]
                    dp_item = (dp_id_item["status_code"], item["value"])
                    logger.debug(
                        f"mq _on_device_report before strategy convert strategy_name={strategy_name},dp_item={dp_item},config_item={config_item}")
                    code, value = strategy.convert(strategy_name, dp_item, config_item)
                    logger.debug(f"mq _on_device_report after strategy convert code={code},value={value}")
                    device.status[code] = value
        else:
            for item in status:
                if "code" in item and "value" in item:
                    code = item["code"]
                    value = item["value"]
                    device.status[code] = value

        self.__update_device(device)

    def _on_device_other(self, device_id: str, biz_code: str, data: dict[str, Any]):
        logger.debug(f"mq _on_device_other-> {device_id} -- {biz_code}")

        # bind device to user
        if biz_code == BIZCODE_BIND_USER:
            device_ids = [device_id]
            # wait for es sync
            time.sleep(1)

            self._update_device_list_info_cache(device_ids)

            if device_id in self.device_map.keys():
                device = self.device_map.get(device_id)
                self.mq.subscribe_device(device_id, device)
                for listener in self.device_listeners:
                    listener.add_device(device)

        # device status update
        device = self.device_map.get(device_id, None)
        if not device:
            return

        if biz_code == BIZCODE_ONLINE:
            device.online = True
            self.__update_device(device)
        elif biz_code == BIZCODE_OFFLINE:
            device.online = False
            self.__update_device(device)
        elif biz_code == BIZCODE_NAME_UPDATE:
            device.name = data["bizData"]["name"]
            self.__update_device(device)
        elif biz_code == BIZCODE_DPNAME_UPDATE:
            pass
        elif biz_code == BIZCODE_DELETE:
            del self.device_map[device_id]
            self.mq.un_subscribe_device(device_id, device.support_local)
            for listener in self.device_listeners:
                listener.remove_device(device.id)

    def add_device_listener(self, listener: SharingDeviceListener):
        """Add device listener."""
        self.device_listeners.add(listener)

    def remove_device_listener(self, listener: SharingDeviceListener):
        """Remove device listener."""
        self.device_listeners.remove(listener)

    def unload(self):
        self.user_repository.unload(self.terminal_id)


class SharingDeviceListener(metaclass=ABCMeta):
    """Sharing device listener."""

    @abstractclassmethod
    def update_device(self, device: CustomerDevice):
        """Update device info.

        Args:
            device(CustomerDevice): updated device info
        """
        pass

    @abstractclassmethod
    def add_device(self, device: CustomerDevice):
        """Device Added.

        Args:
            device(CustomerDevice): Device added
        """
        pass

    @abstractclassmethod
    def remove_device(self, device_id: str):
        """Device removed.

        Args:
            device_id(str): device's id which removed
        """
        pass
