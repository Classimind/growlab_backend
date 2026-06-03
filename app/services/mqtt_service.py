import paho.mqtt.client as mqtt
import asyncio
from dotenv import load_dotenv
import os
import logging
from typing import Union

load_dotenv()

logger = logging.getLogger(__name__)

class MqttService:
    
    def __init__(self,username,password,broker_url="localhost",broker_port=1883):
        self.client = mqtt.Client(client_id="backend_subscriber",clean_session=False)
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.service = None

        self.client.username_pw_set(self.username,self.password)

        # self.client.on_connect = self.on_connect
        # self.client.on_message = self.on_message

        self.loop = None 

        
    async def start(self,loop):
         # lazy initalize 
         from app.services.actuator_status_service import ActuatorStatusService
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
        logger.info("MQTT stopped")

    # def on_connect(self,client,userdata,flags,rc):
    #     logger.info(f"Connected with result code {rc}")
    #     #subscribe to all actuators
    #     client.subscribe("actuators/+/+/status")
    
    def publish(self, topic: str, data: str, qos: int = 1, retain: bool = False):
        topic = f'actuators/{topic}/status'
        if not self.client.is_connected():
            logger.warning("MQTT client not connected, attempting to reconnect...")
            self.client.reconnect()
        result = self.client.publish(topic, payload=data, qos=qos, retain=retain)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True
        else:
            return False
    

    def on_message(self,client,userdata,msg):
        from app.services.ws_connection_manager import manager
        payload = msg.payload.decode('utf-8').lower()
        async def handle_message():
            try:
                actuator_name = msg.topic.split("/")[2] 
                farm_name = msg.topic.split("/")[1]
                logger.info(f"Received status for {actuator_name}:{payload}")

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
                logger.exception(f"Error handling MQTT message:{e}")
        
        if self.loop:
            asyncio.run_coroutine_threadsafe(handle_message(), self.loop)
        else: 
            logger.warning("Main loop not set. Messagge not processed")


mqtt_service = MqttService("hydroponics","hydroponics@",os.getenv("BROKER_URL"))




