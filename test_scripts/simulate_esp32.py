"""
simulate_esp32.py
------------------------------------------------------
Pretends to be the ESP32 — publishes fake sensor readings over MQTT
to the same broker/topic your real backend subscribes to. Lets you
test the full pipeline (MQTT -> backend -> Random Forest -> dashboard)
without needing the physical hardware yet.

Run: python simulate_esp32.py
Stop with Ctrl+C.
"""

import json
import time
import random
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Load the same .env file used by the backend
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = "firesentinel/sensors"

client = mqtt.Client(client_id="firesentinel-esp32-simulator")
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set()  # HiveMQ Cloud requires TLS
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_start()

print(f"Connected. Publishing simulated sensor data to '{MQTT_TOPIC}' every 3s...")
print("Press Ctrl+C to stop.\n")

phase = 0  # cycles through Normal -> Warning -> Fire -> back to Normal

try:
    while True:
        phase = (phase + 1) % 12

        if phase < 7:
            flame = random.uniform(3200, 4000)
            smoke = random.uniform(120, 220)
            temp = random.uniform(22, 26)
            hum = random.uniform(48, 60)
            scenario = "Normal"
        elif phase < 10:
            flame = random.uniform(2000, 2800)
            smoke = random.uniform(500, 800)
            temp = random.uniform(33, 39)
            hum = random.uniform(35, 45)
            scenario = "Warning"
        else:
            flame = random.uniform(300, 1000)
            smoke = random.uniform(2000, 3500)
            temp = random.uniform(55, 75)
            hum = random.uniform(15, 25)
            scenario = "Fire"

        payload = {
            "flame_value": round(flame, 1),
            "smoke_ppm": round(smoke, 1),
            "temperature_c": round(temp, 1),
            "humidity_pct": round(hum, 1),
            "local_status": {"Normal": 0, "Warning": 1, "Fire": 2}[scenario]
        }

        client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"[{scenario}] Published: {payload}")

        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopping simulator...")
    client.loop_stop()
    client.disconnect()