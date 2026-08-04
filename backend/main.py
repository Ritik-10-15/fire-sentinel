"""
FireSentinel Backend (FastAPI)
------------------------------------------------------
- Subscribes to the same MQTT topic the ESP32 publishes to.
- Runs the Random Forest model on every incoming reading (more accurate
  than the on-device Decision Tree, since it isn't constrained by ESP32's
  limited compute).
- Keeps recent readings in memory + broadcasts live updates over WebSocket
  so the React dashboard updates in real time.
- Exposes REST endpoints for history / current status.

Run:
  pip install fastapi uvicorn paho-mqtt scikit-learn joblib pydantic
  uvicorn main:app --reload --port 8000
"""

import json
import threading
from collections import deque
from datetime import datetime, timezone

import joblib
import pandas as pd
import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------- CONFIG ----------------
import os
from dotenv import load_dotenv
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
MQTT_TOPIC = "firesentinel/sensors"

STATUS_LABELS = {0: "Normal", 1: "Warning", 2: "Fire"}
HISTORY_MAXLEN = 500

# ---------------- APP + MODEL ----------------
app = FastAPI(title="FireSentinel API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your dashboard's domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("random_forest.joblib")
FEATURES = ["flame_value", "smoke_ppm", "temperature_c", "humidity_pct"]

history = deque(maxlen=HISTORY_MAXLEN)
latest_reading = {}
connected_sockets: list[WebSocket] = []
main_event_loop = None  # set on startup, needed to broadcast from the MQTT thread


class Reading(BaseModel):
    flame_value: float
    smoke_ppm: float
    temperature_c: float
    humidity_pct: float
    local_status: int | None = None


def classify(reading: dict) -> dict:
    X = pd.DataFrame([[reading[f] for f in FEATURES]], columns=FEATURES)
    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0].tolist()
    return {
        "status_code": pred,
        "status_label": STATUS_LABELS[pred],
        "confidence": round(max(proba), 4),
    }


async def _broadcast(payload: dict):
    for ws in list(connected_sockets):
        try:
            await ws.send_json(payload)
        except Exception:
            connected_sockets.remove(ws)


def broadcast_sync(payload: dict):
    """Called from the MQTT thread; hands the coroutine off to the main
    FastAPI event loop, since WebSocket sends aren't thread-safe otherwise."""
    import asyncio
    if main_event_loop is not None:
        asyncio.run_coroutine_threadsafe(_broadcast(payload), main_event_loop)


# ---------------- MQTT ----------------
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        rf_result = classify(data)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
            "rf_status_code": rf_result["status_code"],
            "rf_status_label": rf_result["status_label"],
            "rf_confidence": rf_result["confidence"],
        }
        history.append(record)
        latest_reading.update(record)
        broadcast_sync(record)
        print(f"[MQTT] {record}")
    except Exception as e:
        print(f"[MQTT] Failed to process message: {e}")


def start_mqtt_thread():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()  # remove if using plain (unencrypted) port 1883
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


@app.on_event("startup")
async def startup_event():
    import asyncio
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()
    t = threading.Thread(target=start_mqtt_thread, daemon=True)
    t.start()


# ---------------- REST ENDPOINTS ----------------
@app.get("/")
def root():
    return {"service": "FireSentinel API", "status": "running"}


@app.get("/status/latest")
def get_latest():
    return latest_reading or {"message": "No readings yet"}


@app.get("/status/history")
def get_history(limit: int = 100):
    return list(history)[-limit:]


@app.post("/predict")
def predict_manual(reading: Reading):
    """Manually classify a reading — useful for testing without hardware."""
    result = classify(reading.dict())
    return {**reading.dict(), **result}


# ---------------- WEBSOCKET (live dashboard updates) ----------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_sockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive; dashboard doesn't need to send anything meaningful
    except WebSocketDisconnect:
        connected_sockets.remove(websocket)