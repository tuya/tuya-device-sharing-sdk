from __future__ import annotations

from typing import Any, Tuple, Dict

from .customerapi import CustomerApi
import requests

URL_PATH = "apigw.iotbing.com"


class LoginControl:
    def __init__(self):
        self.session = requests.session()

    def qr_code(self, client_id: str, schema: str, user_code: str) -> Dict[str, Any]:
        response = self.session.request("POST",
                                        f"https://{URL_PATH}/v1.0/m/life/home-assistant/qrcode/tokens?clientid={client_id}&usercode={user_code}&schema={schema}",
                                        params=None, json=None, headers=None)
        return response.json()

    def login_result(self, token: str, client_id: str, user_code: str) -> Tuple[bool, Dict[str, Any]]:
        response = self.session.request("GET",
                                        f"https://{URL_PATH}/v1.0/m/life/home-assistant/qrcode/tokens/{token}?clientid={client_id}&usercode={user_code}",
                                        params=None, json=None, headers=None)
        response = response.json()
        if response.get("success"):
            ret = response.get("result", {})
            ret["t"] = response.get("t")
            return True, ret

        return False, response


class UserRepository:
    def __init__(self, customer_api: CustomerApi):
        self.api = customer_api

    def unload(self, terminal_id: str):
        self.api.refresh_access_token_if_need()
        self.api.post("/v1.0/m/token/terminal/expire", None, {
            "accessToken": self.api.token_info.access_token,
            "terminalId": terminal_id
        })

    def user_version_report(self, system_version: str, ty_plugin_version: str, ty_sdk_version: str):
        self.api.post("/v1.0/m/life/home-assistant/qrcode/versions", None, {
            "system_version": system_version,
            "ty_plugin_version": ty_plugin_version,
            "ty_sdk_version": ty_sdk_version
        })
