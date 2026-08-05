import paho.mqtt.client as mqtt
BROKER = "mqtt.safalstha.com.np"
PORT = 1883
TOPIC = "actuators/+/status"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to broker")
        # Subscribe ONLY after successful connection
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to {TOPIC}")
    else:
        print("❌ Connection failed with code", rc)

def on_message(client, userdata, msg):
    print(f"📥 Topic: {msg.topic}")
    print(f"📦 Message: {msg.payload.decode()}")
    print("-" * 40)

client = mqtt.Client()

client.username_pw_set("hydroponics", "hydroponics@")

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

# Start processing network traffic
client.loop_forever()
