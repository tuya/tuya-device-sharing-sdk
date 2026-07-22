"""Sharing Open IOT HUB which base on MQTT."""

from __future__ import annotations

import threading
from .customerapi import CustomerApi
from typing import Any, Callable
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
    def __init__(
        self, customer_api: CustomerApi, owner_ids: list, device: list[CustomerDevice]
    ):
        super().__init__()
        self.api = customer_api
        self._stop_event = threading.Event()
        # Wakes run() early (before the 2h expiry) when a reconnect is needed,
        # e.g. auth failure (rc=5) or an unexpected disconnect. run() then
        # re-establishes the connection with freshly issued credentials.
        self._wakeup = threading.Event()
        self.client = None
        self.mq_config = None
        self.message_listeners = set()
        self.owner_ids = owner_ids
        self.device = device

    def _get_mqtt_config(self) -> SharingMQConfig:
        link_id = f"tuya-device-sharing-sdk-python.{uuid.uuid1()}"
        response = self.api.post(
            "/v1.0/m/life/ha/access/config", None, {"linkId": link_id}
        )
        if (response.get("success"), False) is False:
            raise Exception("get mqtt config error.")

        return SharingMQConfig(response)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.error(f"Unexpected disconnection.{rc}")
            # paho auto-reconnect is disabled (reconnect_on_failure=False), so
            # ask run() to reconnect with fresh credentials instead of letting
            # this client retry with its now-stale client_id.
            if not self._stop_event.is_set():
                self._wakeup.set()
        else:
            logger.debug("disconnect")

    def _on_connect(self, mqttc: mqtt.Client, user_data: Any, flags, rc):
        logger.debug(f"connect flags->{flags}, rc->{rc}")
        if rc == 0:
            for owner_id in self.owner_ids:
                mqttc.subscribe(self.mq_config.owner_topic.format(ownerId=owner_id))
            batch_size = 20
            for i in range(0, len(self.device), batch_size):
                batch_devices = self.device[i : i + batch_size]
                topics_to_subscribe = []
                for dev in batch_devices:
                    dev_id = dev.id
                    topic_str = self.subscribe_topic(dev_id, dev.support_local)
                    topics_to_subscribe.append((topic_str, 0))  # 指定主题和qos=0

                if topics_to_subscribe:
                    mqttc.subscribe(topics_to_subscribe)

        elif rc == CONNECT_FAILED_NOT_AUTHORISED:
            # Runs on this client's paho network-loop thread; must NOT rebuild
            # the connection here (would leak this client and spawn nested
            # clients). Signal run() to refresh credentials and reconnect.
            logger.error(
                "MQTT auth failed (rc=5); requesting reconnect with fresh credentials"
            )
            self._wakeup.set()

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
                self._wakeup.clear()
                self.__run_mqtt()
            except Exception as e:
                # Includes API failures (RequestException) and connect errors
                # (e.g. broker down -> OSError). Back off before retrying so a
                # persistent failure cannot spin into a request/connect storm.
                logger.exception(e)
                logger.error(
                    f"failed to (re)connect mqtt, retrying in {backoff_seconds} seconds."
                )
                self._stop_event.wait(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 60)
                continue

            # Connected. Wait until ~60s before expiry (normal 2h renewal), or
            # until a reconnect is requested early (auth failure / drop).
            reconnect_requested = self._wakeup.wait(self.mq_config.expire_time - 60)
            if self._stop_event.is_set():
                break
            if reconnect_requested:
                # Early drop/auth-failure: throttle with growing backoff so a
                # flapping broker cannot trigger a reconnect storm (each attempt
                # is a fresh credential fetch). A clean renewal at expiry keeps
                # backoff at 1 and reconnects immediately.
                self._stop_event.wait(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 60)
            else:
                backoff_seconds = 1

    def __run_mqtt(self):
        mq_config = self._get_mqtt_config()

        self.mq_config = mq_config

        logger.debug(f"connecting {mq_config.url}")
        mqttc = self._start(mq_config)

        if self.client:
            self._teardown(self.client)
        self.client = mqttc

    def _teardown(self, client: mqtt.Client):
        """Fully dispose of a paho client: disconnect and stop its loop thread.

        Without loop_stop() the background network thread keeps running and,
        combined with auto-reconnect, would keep re-authenticating with this
        client's now-stale client_id. Only ever called from a thread other than
        the client's own loop thread, so loop_stop() cannot deadlock.
        """
        try:
            client.disconnect()
        except Exception as e:
            logger.error("mq disconnect error %s", e)
        try:
            client.loop_stop()
        except Exception as e:
            logger.error("mq loop_stop error %s", e)

    def _start(self, mq_config: SharingMQConfig) -> mqtt.Client:
        # reconnect_on_failure=False: the SDK manages reconnection itself (with
        # freshly issued credentials); paho's built-in reconnect would reuse
        # this client's fixed client_id, which becomes stale after renewal.
        mqttc = mqtt.Client(client_id=mq_config.client_id, reconnect_on_failure=False)
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
        self._stop_event.set()
        self._wakeup.set()
        if self.client:
            self._teardown(self.client)
        self.client = None

    def add_message_listener(self, listener: Callable[[dict], None]):
        """Add mqtt message listener."""
        self.message_listeners.add(listener)

    def remove_message_listener(self, listener: Callable[[dict], None]):
        """Remvoe mqtt message listener."""
        self.message_listeners.discard(listener)
