from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Nested dict: farm_name -> actuator_name -> list of WebSockets
        self.active_connections: dict[str, dict[str, list[WebSocket]]] = {}

    async def connect(self, farm_name: str, actuator_name: str, websocket: WebSocket):
        await websocket.accept()
        if farm_name not in self.active_connections:
            self.active_connections[farm_name] = {}
        if actuator_name not in self.active_connections[farm_name]:
            self.active_connections[farm_name][actuator_name] = []
        self.active_connections[farm_name][actuator_name].append(websocket)
        print(f"Connected {websocket} to {farm_name}/{actuator_name}")

    def disconnect(self, farm_name: str, actuator_name: str, websocket: WebSocket):
        if farm_name in self.active_connections:
            if actuator_name in self.active_connections[farm_name]:
                self.active_connections[farm_name][actuator_name].remove(websocket)
                if not self.active_connections[farm_name][actuator_name]:
                    del self.active_connections[farm_name][actuator_name]
            if not self.active_connections[farm_name]:
                del self.active_connections[farm_name]

    async def broadcast(self, farm_name: str, actuator_name: str, message: dict):
        if farm_name in self.active_connections:
            if actuator_name in self.active_connections[farm_name]:
                for connection in self.active_connections[farm_name][actuator_name]:
                    await connection.send_json(message)

manager = ConnectionManager()