import paho.mqtt.client as mqtt

# MQTT broker info
broker = "mqtt.safalstha.com.np"
port = 1883
username = "hydroponics"
password = "hydroponics"
topic = "actuators/farm2/led1/status"

# Connect to MQTT broker
client = mqtt.Client()
client.username_pw_set(username, password)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print("Failed to connect, return code:", rc)

client.on_connect = on_connect

client.connect(broker, port, 60)
client.loop_start()  # Start network loop in background

# Function to send ON/OFF
def control_led(state):
    if state.upper() not in ["ON", "OFF"]:
        print("State must be 'ON' or 'OFF'")
        return
    result = client.publish(topic, state.upper())
    status = result[0]
    if status == 0:
        print(f"Sent '{state.upper()}' to topic {topic}")
    else:
        print(f"Failed to send message to topic {topic}")

while True:
    cmd = input("Enter LED state (ON/OFF/exit): ")
    if cmd.lower() == "exit":
        break
    control_led(cmd)

client.loop_stop()
client.disconnect()
