import paho.mqtt.client as mqtt
import asyncio

class MqttService:
    
    def __init__(self,username,password,broker_url="localhost",broker_port=1883):
        self.client = mqtt.Client(client_id="backend_subscriber",clean_session=False)
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.service = None

        self.client.username_pw_set(self.username,self.password)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.loop = None 

        
    async def start(self,loop):
         # lazy initalize 
         from services.actuator_status_service import ActuatorStatusService
         """Start the MQTT client loop"""
         self.loop = loop
         # init the actuator status service
         self.service= ActuatorStatusService()
         # connect mqtt client
         self.client.connect_async(self.broker_url,self.broker_port,60)
         self.client.loop_start()


    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT stopped")

    def on_connect(self,client,userdata,flags,rc):
        print(f"Conneccted with result code {rc}")
        #subscribe to all actuators
        client.subscribe("actuators/+/+/status")
    
    def on_message(self,client,userdata,msg):
        from services.ws_connection_manager import manager
        payload = msg.payload.decode('utf-8').lower()
        async def handle_message():
            try:
                actuator_name = msg.topic.split("/")[2] 
                farm_name = msg.topic.split("/")[1]
                print(f"Received status for {actuator_name}:{payload}")

                await self.service.create_status({
                    "actuator_name": actuator_name,
                    "farm_name":farm_name,
                    "status": payload
                })
                # Push update to WebSocket Clients
                await manager.broadcast(farm_name,actuator_name, {
                    "type": "update",
                    "status": payload
                })
            except Exception as e:
                print(f"Error handling MQTT message:{e}")
        
        if self.loop:
            asyncio.run_coroutine_threadsafe(handle_message(), self.loop)
        else: 
            print("Main loop not set. Messagge not processed")


mqtt_service = MqttService("hydroponics","hydroponics","mqtt.safalstha.com.np")