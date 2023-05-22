"""Tuya scene api."""

from types import SimpleNamespace
from typing import Any
from .customerapi import CustomerApi


class SharingScene(SimpleNamespace):
    """Smart Life Scene.
    Attributes:
        actions(list): scene actions
        enabled(bool): is scene enabled
        name(str): scene name
        scene_id(dict): scene id
        home_id(int): scene home id
    """

    actions: list
    enabled: bool
    name: str
    scene_id: str
    home_id: int


class SceneRepository:
    def __init__(self, customer_api: CustomerApi):
        self.api = customer_api

    def query_scenes(self, home_ids: list) -> list[SharingScene]:
        _scenes = []
        for home_id in home_ids:
            response = self.api.get("/v1.0/m/scene/ha/home/scenes", {"homeId": home_id})
            if response["success"]:
                for item in response["result"]:
                    scene = SharingScene(**item)
                    scene.home_id = home_id
                    _scenes.append(scene)

        return _scenes

    def trigger_scene(self, home_id: str, scene_id: str):
        response = self.api.post("/v1.0/m/scene/ha/trigger", None, {"homeId": home_id, "sceneId": scene_id})
        return response["result"]
