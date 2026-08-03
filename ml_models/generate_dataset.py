"""
Generates a synthetic but realistic sensor dataset for FireSentinel.

Sensors:
- flame_value   : analog flame sensor reading (0-4095 on ESP32 ADC). LOWER value = flame detected (most flame sensors are active-low analog).
- smoke_ppm     : MQ-2 gas/smoke sensor, approximate ppm (0-10000).
- temperature_c : DHT22 temperature in Celsius.
- humidity_pct  : DHT22 humidity in percent.

Label:
- fire_status: 0 = Normal, 1 = Warning (early sign), 2 = Fire (confirmed)

Replace this synthetic data with real logged sensor data once your hardware
is running — just keep the same column names and this pipeline still works.
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 6000

rows = []

def sample_normal(n):
    flame = np.random.uniform(2800, 4095, n)          # no flame -> high reading
    smoke = np.random.normal(150, 60, n).clip(0, 400)  # ambient background smoke/gas
    temp = np.random.normal(24, 3, n).clip(10, 35)
    hum = np.random.normal(55, 10, n).clip(20, 90)
    return flame, smoke, temp, hum, np.zeros(n, dtype=int)

def sample_warning(n):
    # early smoke rise, mild temp rise, no confirmed flame yet
    flame = np.random.uniform(1500, 3200, n)
    smoke = np.random.normal(600, 150, n).clip(300, 1500)
    temp = np.random.normal(35, 5, n).clip(28, 50)
    hum = np.random.normal(40, 12, n).clip(10, 70)
    return flame, smoke, temp, hum, np.ones(n, dtype=int)

def sample_fire(n):
    # flame detected (low reading), high smoke, high temp, low humidity
    flame = np.random.uniform(0, 1200, n)
    smoke = np.random.normal(2500, 900, n).clip(1200, 8000)
    temp = np.random.normal(65, 15, n).clip(45, 120)
    hum = np.random.normal(20, 8, n).clip(5, 45)
    return flame, smoke, temp, hum, np.full(n, 2, dtype=int)

n_each = N // 3
for sampler in (sample_normal, sample_warning, sample_fire):
    flame, smoke, temp, hum, label = sampler(n_each)
    for f, s, t, h, l in zip(flame, smoke, temp, hum, label):
        rows.append([round(f, 1), round(s, 1), round(t, 2), round(h, 2), l])

df = pd.DataFrame(rows, columns=["flame_value", "smoke_ppm", "temperature_c", "humidity_pct", "fire_status"])
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

import os
output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "sensor_data.csv")
df.to_csv(output_path, index=False)
print(df["fire_status"].value_counts())
print(df.head())
print(f"\nSaved {len(df)} rows to data/sensor_data.csv")