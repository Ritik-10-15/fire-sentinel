# FireSentinel — Edge-to-Cloud Fire Detection System

An IoT fire detection architecture built around a simple principle: **safety-critical
alerts shouldn't depend on network uptime.** FireSentinel pairs a lightweight
on-device model for instant, network-independent alerts with a heavier cloud model
for higher-confidence classification — connected by a real-time MQTT pipeline and a
live monitoring dashboard.

**Note on hardware**: This project is validated end-to-end using a software
simulator that publishes realistic sensor data over a real MQTT broker, standing in
for physical hardware. The ESP32 firmware is fully written and hardware-ready, but
has not been flashed to a physical device — the focus of this project is the
software architecture, machine learning pipeline, and real-time systems design.
<img width="1000" height="497" alt="firesentinel_demo" src="https://github.com/user-attachments/assets/c250b370-cd03-4c08-9500-fc87b866ea9b" />

## Why this architecture

Most fire detection demos stop at "sensor triggers alert." This project asks a
harder question: what happens when the network drops at the exact moment a system
needs to work? The answer here is a **dual-layer design**:

- **Edge layer**: a shallow Decision Tree, compiled directly into ESP32 firmware as
  plain C code. No ML runtime needed on-device — just fast if/else comparisons that
  work even if WiFi or the cloud is unreachable.
- **Cloud layer**: a Random Forest served via FastAPI, not constrained by embedded
  compute, so it can be more accurate and serve richer analytics.

## Architecture
- **Edge (ESP32 firmware)**: reads flame, MQ-2 smoke/gas, and DHT22 temp/humidity
  sensors every 5s. Runs a shallow Decision Tree compiled directly into firmware
  (`decision_tree.h`) so alerts work even if WiFi/cloud is down. Publishes readings
  over MQTT and logs to ThingSpeak.
- **Backend (FastAPI)**: subscribes to the MQTT topic, runs a Random Forest model
  on each reading, keeps history in memory, and pushes live updates to the
  dashboard over WebSocket.
- **Dashboard**: a live monitoring panel styled after real fire alarm control
  panels — annunciator status banner, sensor tiles, live trend chart, event log.
  Falls back to a simulated demo mode automatically if no backend is running, so
  it's explorable without any live infrastructure.

## Folder structure
## Setup

### 1. Train the models
```bash
cd ml_models
python generate_dataset.py   # or replace data/sensor_data.csv with real logged readings
python train_models.py       # regenerates decision_tree.h and random_forest.joblib
```

### 2. Set up a free MQTT broker
This project uses [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/) (free
tier). Create a cluster, then create credentials under **Access Management** with
Publish + Subscribe permissions.

### 3. Configure environment variables
Create `backend/.env` (this file is gitignored — never commit real credentials):
### 4. Run the backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
You should see `[MQTT] Connected with result code 0` — confirming a successful,
authenticated connection to the real broker.

### 5. Run the simulated sensor publisher
In a separate terminal:
```bash
cd test_scripts
python simulate_esp32.py
```
This publishes realistic sensor readings over MQTT every 3 seconds, cycling through
Normal → Warning → Fire scenarios — standing in for real hardware.

### 6. Serve and open the dashboard
Browsers block WebSocket connections from `file://` origins, so the dashboard needs
to be served over local HTTP:
```bash
cd dashboard
python -m http.server 5500
```
Open **http://127.0.0.1:5500** in your browser. With the backend and simulator both
running, it should show **"Live — connected to backend"** and display real,
classified sensor data streaming in.

If no backend is running, the dashboard automatically falls into **demo mode** after
3 seconds, simulating data client-side — useful for showcasing the UI without any
infrastructure running at all.

## Testing the model directly
```bash
# Via the FastAPI interactive docs (easiest):
# open http://127.0.0.1:8000/docs -> POST /predict -> Try it out

# Example fire-like reading:
{
  "flame_value": 800,
  "smoke_ppm": 2600,
  "temperature_c": 70,
  "humidity_pct": 15
}
# Expected: "status_label": "Fire", high confidence
```

## Model performance
On the synthetic dataset (6000 rows, 3 balanced classes):
- Decision Tree (on-device): ~99.8% accuracy, macro F1 ~0.998
- Random Forest (backend): ~100% accuracy, macro F1 ~1.0

These numbers are high because the synthetic classes were generated with fairly
separable ranges. Real logged sensor data (via ThingSpeak export or direct logging)
would likely bring real-world accuracy closer to 85–95%, which is expected and
still a strong result — synthetic data is a starting point, not a substitute for
real validation.

Feature importance (Random Forest): smoke_ppm (0.50) > flame_value (0.31) >
temperature_c (0.19) > humidity_pct (0.001).

## Security notes
- MQTT credentials are stored in `backend/.env`, which is gitignored and never
  committed. A `.env.example` (values blanked) can be added for anyone cloning
  this repo to know what to configure.
- This is a personal/educational project; the MQTT credential is not scoped beyond
  publish+subscribe on this project's topic.

## What's simulated vs. real
| Component | Status |
|---|---|
| ML models (Decision Tree, Random Forest) | Real, trained, tested |
| MQTT pipeline (HiveMQ Cloud) | Real, live broker, authenticated |
| Backend (FastAPI, WebSocket, REST API) | Real, running, tested |
| Dashboard | Real, live-data capable |
| Sensor data | Simulated (`simulate_esp32.py`) — no physical sensors used |
| ESP32 firmware | Written, compilable, hardware-ready — not flashed to a device |

## Next steps / ideas
- Flash the firmware to a real ESP32 and calibrate the MQ-2 sensor against a
  reference gas source
- Add a buzzer/siren escalation and SMS/push notification on "Fire" status
- Persist history to a real database (SQLite/Postgres) instead of an in-memory deque
- Add authentication before exposing the dashboard publicly
- Replace synthetic training data with real logged sensor readings
