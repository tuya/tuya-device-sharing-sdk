"""Sharing Open IOT HUB which base on MQTT."""
from __future__ import annotations

import threading
from .customerapi import CustomerApi
from typing import Any, Callable
from requests.exceptions import RequestException
import time
from .customerlogging import logger
from .device import CustomerDevice
from paho.mqtt import client as mqtt
from urllib.parse import urlsplit
import json
import uuid

CONNECT_FAILED_NOT_AUTHORISED = 5


class SharingMQConfig:
    """Sharing mqtt config."""

    def __init__(self, mqConfigResponse: dict[str, Any] = {}) -> None:
        """Init SharingMQConfig."""
        result = mqConfigResponse.get("result", {})
        self.url = result.get("url", "")
        self.client_id = result.get("clientId", "")
        self.username = result.get("username", "")
        self.password = result.get("password", "")
        self.expire_time = result.get("expireTime", 0)
        self.owner_topic = result.get("topic").get("ownerId").get("sub")
        self.dev_topic = result.get("topic").get("devId").get("sub")


class SharingMQ(threading.Thread):
    def __init__(self, customer_api: CustomerApi, owner_ids: list, device: list[CustomerDevice]):
        super().__init__()
        self.api = customer_api
        self._stop_event = threading.Event()
        self.client = None
        self.mq_config = None
        self.message_listeners = set()
        self.owner_ids = owner_ids
        self.device = device

    def _get_mqtt_config(self) -> SharingMQConfig:
        link_id = f"tuya-device-sharing-sdk-python.{uuid.uuid1()}"
        response = self.api.post("/v1.0/m/life/ha/access/config", None,
                                 {"linkId": link_id})
        if (response.get("success"), False) is False:
            raise Exception("get mqtt config error.")

        return SharingMQConfig(response)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.error(f"Unexpected disconnection.{rc}")
        else:
            logger.debug("disconnect")

    def _on_connect(self, mqttc: mqtt.Client, user_data: Any, flags, rc):
        logger.debug(f"connect flags->{flags}, rc->{rc}")
        if rc == 0:
            for owner_id in self.owner_ids:
                mqttc.subscribe(self.mq_config.owner_topic.format(ownerId=owner_id))
            batch_size = 20
            for i in range(0, len(self.device), batch_size):
                batch_devices = self.device[i:i + batch_size]
                topics_to_subscribe = []
                for dev in batch_devices:
                    dev_id = dev.id
                    topic_str = self.subscribe_topic(dev_id, dev.support_local)
                    topics_to_subscribe.append((topic_str, 0))  # 指定主题和qos=0

                if topics_to_subscribe:
                    mqttc.subscribe(topics_to_subscribe)

        elif rc == CONNECT_FAILED_NOT_AUTHORISED:
            self.__run_mqtt()

    def subscribe_device(self, dev_id: str, device: CustomerDevice):
        self.device.append(device)
        topic = self.subscribe_topic(dev_id, device.support_local)
        self.client.subscribe(topic)

    def un_subscribe_device(self, dev_id: str, support_local: bool):
        topic = self.subscribe_topic(dev_id, support_local)
        self.client.unsubscribe(topic)

    def subscribe_topic(self, dev_id: str, support_local: bool) -> str:
        subscribe_topic = self.mq_config.dev_topic.format(devId=dev_id)
        if support_local:
            subscribe_topic += "/pen"
        else:
            subscribe_topic += "/sta"
        return subscribe_topic

    def _on_message(self, mqttc: mqtt.Client, user_data: Any, msg: mqtt.MQTTMessage):
        logger.debug(f"payload-> {msg.payload}")

        msg_dict = json.loads(msg.payload.decode("utf8"))

        logger.debug(f"on_message: {msg_dict}")

        for listener in self.message_listeners:
            listener(msg_dict)

    def _on_subscribe(self, mqttc: mqtt.Client, user_data: Any, mid, granted_qos):
        logger.debug(f"_on_subscribe: {mid}")

    def _on_log(self, mqttc: mqtt.Client, user_data: Any, level, string):
        logger.debug(f"_on_log: {string}")

    def run(self):
        """Method representing the thread's activity which should not be used directly."""
        backoff_seconds = 1
        while not self._stop_event.is_set():
            try:
                self.__run_mqtt()
                backoff_seconds = 1

                # reconnect every 2 hours required.
                time.sleep(self.mq_config.expire_time - 60)
            except RequestException as e:
                logger.exception(e)
                logger.error(f"failed to refresh mqtt server, retrying in {backoff_seconds} seconds.")

                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 60)  # Try at most every 60 seconds to refresh

    def __run_mqtt(self):
        mq_config = self._get_mqtt_config()

        self.mq_config = mq_config

        logger.debug(f"connecting {mq_config.url}")
        mqttc = self._start(mq_config)

        if self.client:
            self.client.disconnect()
        self.client = mqttc

    def _start(self, mq_config: SharingMQConfig) -> mqtt.Client:
        mqttc = mqtt.Client(mq_config.client_id)
        mqttc.username_pw_set(mq_config.username, mq_config.password)
        mqttc.user_data_set({"mqConfig": mq_config})
        mqttc.on_connect = self._on_connect
        mqttc.on_message = self._on_message
        mqttc.on_subscribe = self._on_subscribe
        mqttc.on_log = self._on_log
        mqttc.on_disconnect = self._on_disconnect

        url = urlsplit(mq_config.url)
        if url.scheme == "ssl":
            mqttc.tls_set()

        mqttc.connect(url.hostname, url.port)

        mqttc.loop_start()
        return mqttc

    def start(self):
        """Start mqtt.

        Start mqtt thread
        """
        logger.debug("start")
        super().start()

    def stop(self):
        """Stop mqtt.

        Stop mqtt thread
        """
        logger.debug("stop")
        self.message_listeners = set()
        try:
            self.client.disconnect()
        except Exception as e:
            logger.error("mq disconnect error %s", e)
        self.client = None
        self._stop_event.set()

    def add_message_listener(self, listener: Callable[[dict], None]):
        """Add mqtt message listener."""
        self.message_listeners.add(listener)

    def remove_message_listener(self, listener: Callable[[dict], None]):
        """Remvoe mqtt message listener."""
        self.message_listeners.discard(listener)
