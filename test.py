import paho.mqtt.client as mqtt

# Callback when message is received
def on_message(client, userdata, msg):
    print(f"Received message from topic {msg.topic}: {msg.payload.decode()}")

# Create client
client = mqtt.Client()

# Set username and password
client.username_pw_set(username="emqx_u", password="EMQemq@1172")

# Connect to EMQX broker
client.connect("mqtt.safalstha.com.np", 1883, 60)  # replace 'localhost' with your broker IP

# Assign callback
client.on_message = on_message

# Subscribe to a specific sensor
sensor_id = "123"
client.subscribe(f"/sensor/{sensor_id}")

# Or subscribe to all sensors
# client.subscribe("/sensor/+")

# Start the loop
client.loop_forever()
