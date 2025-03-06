import paho.mqtt.client as mqtt
import json

# MQTT broker details
broker = "localhost"
port = 1883
topic = "zigbee2mqtt/0xa4c1383030570883"

# Callback function to handle incoming messages
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    print(f"Received message: {payload}")

# Function to control the state of the device
def control_device(state):
    payload = json.dumps({"state": state})
    client.publish(topic + "/set", payload)
    print(f"Sent message: {payload}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback function to the client
client.on_message = on_message

# Connect to the MQTT broker
client.connect(broker, port)

# Subscribe to the topic to read power measurements
client.subscribe(topic)

# Start the MQTT client loop in a separate thread
client.loop_start()

# Example usage: Control the device state and read power measurements
#control_device("ON")
control_device("OFF")

# Keep the script running to listen for incoming messages
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting...")

# Stop the MQTT client loop and disconnect
client.loop_stop()
client.disconnect()