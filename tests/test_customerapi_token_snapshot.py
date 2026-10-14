"""Requests must use one access/refresh token generation throughout signing."""

import hashlib
import json
import time
import unittest
from unittest.mock import Mock, patch

from tuya_sharing import customerapi


class TokenSnapshotTest(unittest.TestCase):
    def test_refresh_during_encryption_keeps_signature_and_header_consistent(self):
        old = customerapi.CustomerTokenInfo({
            "t": int(time.time() * 1000), "expire_time": 3600,
            "access_token": "old-access", "refresh_token": "old-refresh",
        })
        new = customerapi.CustomerTokenInfo({
            "t": int(time.time() * 1000), "expire_time": 3600,
            "access_token": "new-access", "refresh_token": "new-refresh",
        })
        api = customerapi.CustomerApi(old, "client", "user", "https://example.invalid", None)
        response = Mock(ok=True)
        response.json.return_value = {"success": True}
        api.session.request = Mock(return_value=response)
        encrypt = customerapi._aes_gcm_encrypt

        def rotate(raw, secret):
            # The refresh worker publishes a new pair while this request is
            # encrypting its payload, after deriving the old pair's key.
            api.token_info = new
            return encrypt(raw, secret)

        with patch.object(customerapi, "_aes_gcm_encrypt", side_effect=rotate):
            self.assertEqual(api.post("/scene", body={"sceneId": "test"}), {"success": True})
        request = api.session.request.call_args.kwargs
        headers = request["headers"]
        self.assertEqual(headers["X-token"], old.access_token)
        key = hashlib.md5((headers["X-requestId"] + old.refresh_token).encode()).hexdigest()
        self.assertEqual(headers["X-sign"], customerapi._restful_sign(
            key, "", request["json"]["encdata"], headers,
        ))
        self.assertIs(api.token_info, new)

    def test_request_after_refresh_uses_new_pair(self):
        old = customerapi.CustomerTokenInfo({"access_token": "old", "refresh_token": "old"})
        new = customerapi.CustomerTokenInfo({"access_token": "new", "refresh_token": "new"})
        api = customerapi.CustomerApi(old, "client", "user", "https://example.invalid", None)
        api.refresh_access_token_if_need = lambda: setattr(api, "token_info", new)
        response = Mock(ok=True)
        response.json.return_value = {"success": True}
        api.session.request = Mock(return_value=response)
        api.get("/devices")
        headers = api.session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["X-token"], new.access_token)
        key = hashlib.md5((headers["X-requestId"] + new.refresh_token).encode()).hexdigest()
        self.assertEqual(headers["X-sign"], customerapi._restful_sign(key, "", "", headers))

    def test_expired_token_refresh_omits_access_token_and_uses_rotated_pair(self):
        api = customerapi.CustomerApi(customerapi.CustomerTokenInfo({
            "access_token": "expired", "refresh_token": "refresh-old",
        }), "client", "user", "https://example.invalid", None)
        calls = []

        def request(method, url, **kwargs):
            headers = kwargs["headers"]
            calls.append((url, kwargs))
            response = Mock(ok=True)
            if "/token/" in url:
                self.assertNotIn("X-token", headers)
                key = hashlib.md5((headers["X-requestId"] + "refresh-old").encode()).hexdigest()
                secret = customerapi._secret_generating(headers["X-requestId"], "", key)
                result = {"expireTime": 7200, "uid": "user",
                          "accessToken": "access-new", "refreshToken": "refresh-new"}
                response.json.return_value = {
                    "success": True, "t": int(time.time() * 1000),
                    "result": customerapi._aes_gcm_encrypt(json.dumps(result), secret).decode(),
                }
            else:
                self.assertEqual(headers["X-token"], "access-new")
                response.json.return_value = {"success": True}
            return response

        api.session.request = request
        self.assertEqual(api.get("/devices"), {"success": True})
        self.assertEqual(len(calls), 2)
        api.get("/devices")
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(kwargs["timeout"] == customerapi.DEFAULT_TIMEOUT
                            for _, kwargs in calls))

    def test_api_error_preserves_typed_exception(self):
        api = customerapi.CustomerApi(customerapi.CustomerTokenInfo({
            "t": int(time.time() * 1000), "expire_time": 7200,
            "access_token": "access", "refresh_token": "refresh",
        }), "client", "user", "https://example.invalid", None)
        response = Mock(ok=True)
        response.json.return_value = {"success": False, "code": 1010, "msg": "token invalid"}
        api.session.request = Mock(return_value=response)
        with self.assertRaises(customerapi.ApiRequestException):
            api.get("/devices")
