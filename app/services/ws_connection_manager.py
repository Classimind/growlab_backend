from fastapi import WebSocket
from typing import Dict,List,Union
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # Nested dict: farm_name -> actuator_name -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, actuatorId: str, websocket: WebSocket):
        await websocket.accept()
        if actuatorId not in self.active_connections:
            self.active_connections[actuatorId] = []
        self.active_connections[actuatorId].append(websocket)
    
    def disconnect(self, actuatorId: str, websocket: WebSocket):
        if actuatorId in self.active_connections and websocket in self.active_connections[actuatorId]:
            self.active_connections[actuatorId].remove(websocket)
    
    def serialize_sensor_data(self,data: dict) -> dict:
        data = data.copy()
        if "created" in data and isinstance(data["created"], datetime):
            data["created"] = data["created"].isoformat()  # convert to ISO string
        return data


    async def send_update(self, actuatorId: str, value: Union[str,float,int]):
        if actuatorId in self.active_connections:
            for ws in self.active_connections[actuatorId]:
                try:
                    await ws.send_json({"type":"update","status":value})
                except  Exception as e:
                    self.disconnect(actuatorId, ws)

    # async def broadcast(self, farm_name: str, actuator_name: str, message: dict):
    #     if farm_name in self.active_connections:
    #         if actuator_name in self.active_connections[farm_name]:
    #             for connection in self.active_connections[farm_name][actuator_name]:
    #                 await connection.send_json(message)

manager = ConnectionManager()