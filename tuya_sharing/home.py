from __future__ import annotations

from .customerapi import CustomerApi


class SmartLifeHome:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name


class SmartLifeRoom:
    def __init__(self, id: str, name: str, display_order: int = 0):
        self.id = id
        self.name = name
        self.display_order = display_order


class HomeRepository:
    def __init__(self, customer_api: CustomerApi):
        self.api = customer_api

    def query_homes(self) -> list[SmartLifeHome]:
        response = self.api.get("/v1.0/m/life/users/homes")

        if response.get("success", False):
            _homes = []
            for home in response["result"]:
                _home = SmartLifeHome(str(home["ownerId"]), home["name"])
                _homes.append(_home)
            return _homes

        return []

    def query_room_by_device(self, device_id: str) -> SmartLifeRoom | None:
        response = self.api.get(f"/v1.0/m/thing/ha/{device_id}/room")

        if response.get("success", False):
            room = response.get("result")
            if room:
                return SmartLifeRoom(
                    str(room["id"]), room["name"], room.get("displayOrder", 0)
                )

        return None
