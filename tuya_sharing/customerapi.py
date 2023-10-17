"""Customer API."""
from __future__ import annotations

from typing import Any
import requests
from .customerlogging import logger
import json
import hmac
import hashlib
import random
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import uuid
from abc import ABCMeta

import time


class CustomerTokenInfo:
    """CUstomer token info.

    Attributes:
        access_token: Access token.
        expire_time: Valid period in seconds.
        refresh_token: Refresh token.
    """

    def __init__(self, token_info: dict[str, Any] = None):
        self.expire_time = (
                token_info.get("t", 0)
                + token_info.get("expire_time", 0) * 1000
        )
        self.uid = token_info.get("uid", "")
        self.access_token = token_info.get("access_token", "")
        self.refresh_token = token_info.get("refresh_token", "")


class CustomerApi:

    def __init__(
            self,
            token_info: CustomerTokenInfo,
            client_id: str,
            user_code: str,
            end_point: str,
            listener: SharingTokenListener
    ):
        self.session = requests.session()
        self.token_info = token_info
        self.client_id = client_id
        self.user_code = user_code
        self.endpoint = end_point
        self.refresh_token = False
        self.token_listener = listener

    def __request(
            self,
            method: str,
            path: str,
            params: dict[str, Any] | None = None,
            body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:

        self.refresh_access_token_if_need()

        rid = str(uuid.uuid4())
        sid = ""
        md5 = hashlib.md5()
        rid_refresh_token = rid + self.token_info.refresh_token
        md5.update(rid_refresh_token.encode('utf-8'))
        hash_key = md5.hexdigest()
        secret = _secret_generating(rid, sid, hash_key)

        query_encdata = ""
        if params is not None and len(params.keys()) > 0:
            query_encdata = _form_to_json(params)
            query_encdata = _aes_gcm_encrypt(query_encdata, secret)
            params = {
                "encdata": query_encdata
            }
            query_encdata = str(query_encdata, encoding="utf8")
        body_encdata = ""
        if body is not None and len(body.keys()) > 0:
            body_encdata = _form_to_json(body)
            body_encdata = _aes_gcm_encrypt(body_encdata, secret)
            body = {
                "encdata": str(body_encdata, encoding="utf8")
            }
            body_encdata = str(body_encdata, encoding="utf8")

        t = int(time.time() * 1000)
        headers = {
            "X-appKey": self.client_id,
            "X-requestId": rid,
            "X-sid": sid,
            "X-time": str(t),
        }
        if self.token_info is not None and len(self.token_info.access_token) > 0:
            headers["X-token"] = self.token_info.access_token

        sign = _restful_sign(hash_key,
                             query_encdata,
                             body_encdata,
                             headers)
        headers["X-sign"] = sign

        response = self.session.request(
            method, self.endpoint + path, params=params, json=body, headers=headers
        )

        if response.ok is False:
            logger.error(
                f"Response error: code={response.status_code}, content={response.content}"
            )
            return None

        ret = response.json()
        logger.debug("response before decrypt ret = %s", ret)

        if not ret.get("success"):
            raise Exception(f"network error:({ret['code']}) {ret['msg']}")

        result = _aex_gcm_decrypt(ret.get("result"), secret)
        try:
            ret["result"] = json.loads(result)
        except json.decoder.JSONDecodeError:
            ret["result"] = result

        logger.debug("response ret = %s", ret)
        return ret

    def refresh_access_token_if_need(self):

        if self.refresh_token:
            return

        now = int(time.time() * 1000)
        expired_time = self.token_info.expire_time

        if expired_time - 60 * 1000 > now:  # 1min
            return

        self.refresh_token = True
        try:
            response = self.get("/v1.0/m/token/" + self.token_info.refresh_token)

            if response.get("success"):
                result = response.get("result", {})
                token_info = {
                    "t": response["t"],
                    "expire_time": result["expireTime"],
                    "uid": result["uid"],
                    "access_token": result["accessToken"],
                    "refresh_token": result["refreshToken"]
                }
                self.token_info = CustomerTokenInfo(token_info)
                if self.token_listener is not None:
                    self.token_listener.update_token(token_info)
        except Exception as e:
            logger.error("net work error = %s", e)
        finally:
            self.refresh_token = False

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Http Get.

        Requests the server to return specified resources.

        Args:
            path (str): api path
            params (map): request parameter

        Returns:
            response: response body
        """
        return self.__request("GET", path, params, None)

    def post(self, path: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[
        str, Any]:
        """Http Post.

        Requests the server to update specified resources.

        Args:
            path (str): api path
            params (map): request parameter
            body (map): request body

        Returns:
            response: response body
        """
        return self.__request("POST", path, params, body)

    def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Http Put.

        Requires the server to perform specified operations.

        Args:
            path (str): api path
            body (map): request body

        Returns:
            response: response body
        """
        return self.__request("PUT", path, None, body)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Http Delete.

        Requires the server to delete specified resources.

        Args:
            path (str): api path
            params (map): request param

        Returns:
            response: response body
        """
        return self.__request("DELETE", path, params, None)


def _random_nonce(e=32):
    t = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
    a = len(t)
    n = ""
    for i in range(e):
        n += t[random.randint(0, a - 1)]
    return n


def _form_to_json(content: dict[str, Any] | None = None) -> str:
    return json.dumps(content, separators=(',', ':'))


def _aes_gcm_encrypt(raw_data: str, secret: str):
    nonce = _random_nonce(12)
    raw_data = raw_data.encode('utf-8')
    secret = secret.encode('utf-8')
    nonce = nonce.encode('utf-8')
    cipher = AESGCM(secret)
    ciphertext = cipher.encrypt(nonce, raw_data, None)

    return base64.b64encode(nonce) + base64.b64encode(ciphertext)


def _aex_gcm_decrypt(cipher_data: str, secret: str) -> str:
    cipher_data = base64.b64decode(cipher_data)
    nonce = cipher_data[:12]
    cipher_text = cipher_data[12:]
    secret = secret.encode('utf-8')
    cipher = AESGCM(secret)
    decrypt = cipher.decrypt(nonce, cipher_text, None)
    return str(decrypt, encoding="utf8")


def _secret_generating(rid, sid, hash_key) -> str:
    message = hash_key
    mod = 16
    if sid != "":
        sid_length = len(sid)
        length = sid_length if sid_length < mod else mod
        ecode = ""
        for i in range(length):
            idx = ord(sid[i]) % mod
            ecode += sid[idx]
        message += "_"
        message += ecode

    if isinstance(message, str):
        message = message.encode('utf-8')
    if isinstance(rid, str):
        rid = rid.encode('utf-8')

    checksum = hmac.new(rid, message, hashlib.sha256)
    byte_temp = checksum.digest()
    secret = byte_temp.hex()

    return secret[:16]


def _restful_sign(hash_key: str, query_encdata: str, body_encdata: str, data: dict[str, Any]) -> str:
    headers = ["X-appKey", "X-requestId", "X-sid", "X-time", "X-token"]
    header_sign_str = ""
    for item in headers:
        val = data.get(item, "")
        if val != "":
            header_sign_str += item + "=" + val + "||"

    sign_str = header_sign_str[:-2]

    if query_encdata is not None and query_encdata != "":
        sign_str += query_encdata
    if body_encdata is not None and body_encdata != "":
        sign_str += body_encdata

    sign_str = bytes(sign_str, 'utf-8')
    hash_key = bytes(hash_key, 'utf-8')

    hash_value = hmac.new(hash_key, sign_str, hashlib.sha256)
    return hash_value.hexdigest()


class SharingTokenListener(metaclass=ABCMeta):
    def update_token(self, token_info: dict[str, Any]):
        """Update token.
        """
        pass
