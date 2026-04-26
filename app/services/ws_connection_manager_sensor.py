from fastapi import  WebSocket
from typing import Dict, List
from app.services.sensor_service import CollectSensorValueService
from datetime import datetime

sensor_service = CollectSensorValueService()


class SensorConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, key: str, websocket: WebSocket):
        await websocket.accept()
        if key not in self.active_connections:
            self.active_connections[key] = []
        self.active_connections[key].append(websocket)

    def disconnect(self, key: str, websocket: WebSocket):
        if key in self.active_connections and websocket in self.active_connections[key]:
            self.active_connections[key].remove(websocket)
    
    def serialize_sensor_data(self,data: dict) -> dict:
        data = data.copy()
        if "created" in data and isinstance(data["created"], datetime):
            data["created"] = data["created"].isoformat()  # convert to ISO string
        return data

    async def send_update(self, key: str, data: dict):
        if key in self.active_connections:
            for ws in self.active_connections[key]:
                try:
                    serialized_data = self.serialize_sensor_data(data)
                    # print(serialized_data)
                    await ws.send_json({"type":"update","data":serialized_data})
                except  Exception as e:
                    # print(e)
                    self.disconnect(key, ws)

sensormanager = SensorConnectionManager()
