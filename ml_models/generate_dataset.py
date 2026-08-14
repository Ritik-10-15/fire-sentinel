"""
Generates a synthetic sensor dataset for FireSentinel — v2, with realistic noise
and class overlap, so the resulting accuracy numbers are actually defensible
rather than an artifact of perfectly separable synthetic ranges.

Sensors:
- flame_value   : analog flame sensor reading (0-4095 on ESP32 ADC). LOWER value = flame detected.
- smoke_ppm     : MQ-2 gas/smoke sensor, approximate ppm (0-10000).
- temperature_c : DHT22 temperature in Celsius.
- humidity_pct  : DHT22 humidity in percent.

Label:
- fire_status: 0 = Normal, 1 = Warning (early sign), 2 = Fire (confirmed)

What changed from v1:
- Wider, overlapping distributions between adjacent classes (a cooking pan or a
  sunny window can look a lot like "Warning" briefly — real sensors don't have
  clean boundaries)
- Occasional sensor noise/dropout spikes (real hardware has moments of noisy
  readings — a spike doesn't always mean what it looks like)
- A small fraction of genuinely ambiguous edge cases deliberately left in, since
  real-world labeling (e.g. "was this actually a fire risk or just someone
  grilling nearby") is never perfectly clean either

Replace this synthetic data with real logged sensor data once hardware is
running — this is a more honest stand-in in the meantime, not a replacement
for real validation.
"""

import numpy as np
import pandas as pd
import os

np.random.seed(42)
N = 6000

rows = []

def sample_normal(n):
    flame = np.random.normal(3400, 500, n).clip(1800, 4095)
    smoke = np.random.gamma(shape=2.0, scale=110, size=n).clip(0, 700)
    temp = np.random.normal(24, 4, n).clip(10, 42)
    hum = np.random.normal(55, 13, n).clip(15, 95)
    return flame, smoke, temp, hum, np.zeros(n, dtype=int)

def sample_warning(n):
    flame = np.random.normal(2400, 650, n).clip(900, 3800)
    smoke = np.random.gamma(shape=2.2, scale=280, size=n).clip(150, 2200)
    temp = np.random.normal(34, 7, n).clip(24, 55)
    hum = np.random.normal(40, 14, n).clip(8, 75)
    return flame, smoke, temp, hum, np.ones(n, dtype=int)

def sample_fire(n):
    flame = np.random.normal(700, 550, n).clip(0, 2200)
    smoke = np.random.gamma(shape=2.5, scale=900, size=n).clip(700, 9000)
    temp = np.random.normal(62, 18, n).clip(35, 130)
    hum = np.random.normal(22, 10, n).clip(3, 55)
    return flame, smoke, temp, hum, np.full(n, 2, dtype=int)

n_each = N // 3
for sampler in (sample_normal, sample_warning, sample_fire):
    flame, smoke, temp, hum, label = sampler(n_each)
    for f, s, t, h, l in zip(flame, smoke, temp, hum, label):
        rows.append([round(f, 1), round(s, 1), round(t, 2), round(h, 2), l])

df = pd.DataFrame(rows, columns=["flame_value", "smoke_ppm", "temperature_c", "humidity_pct", "fire_status"])

# --- Realistic sensor artifacts ---

# 1. Occasional noisy/spiky readings (electrical interference, a passing
#    headlight briefly fooling the flame sensor, etc.) — about 3% of rows get
#    one feature bumped by a random spike, independent of the true label.
n_noisy = int(len(df) * 0.03)
noisy_idx = np.random.choice(df.index, n_noisy, replace=False)
for idx in noisy_idx:
    feature = np.random.choice(["flame_value", "smoke_ppm", "temperature_c", "humidity_pct"])
    if feature == "flame_value":
        df.loc[idx, feature] = np.random.uniform(0, 4095)
    elif feature == "smoke_ppm":
        df.loc[idx, feature] = np.random.uniform(0, 9000)
    elif feature == "temperature_c":
        df.loc[idx, feature] = np.clip(df.loc[idx, feature] + np.random.uniform(-8, 8), 5, 140)
    else:
        df.loc[idx, feature] = np.clip(df.loc[idx, feature] + np.random.uniform(-15, 15), 0, 100)

# 2. A small number of genuinely ambiguous edge cases straddling Normal/Warning
#    (e.g. someone cooking with a lot of smoke, no real fire risk) — labeled
#    Normal despite Warning-like smoke, since this is exactly the kind of case
#    that keeps real-world accuracy below 100%.
n_ambiguous = int(len(df) * 0.02)
ambiguous_idx = np.random.choice(df[df["fire_status"] == 0].index, n_ambiguous, replace=False)
df.loc[ambiguous_idx, "smoke_ppm"] = np.random.uniform(400, 900, n_ambiguous)
df.loc[ambiguous_idx, "temperature_c"] = np.random.uniform(28, 36, n_ambiguous)

df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "sensor_data.csv")
df.to_csv(output_path, index=False)

print(df["fire_status"].value_counts())
print(df.describe())
print(f"\nSaved {len(df)} rows to data/sensor_data.csv (v2 -- realistic noise + overlap)")