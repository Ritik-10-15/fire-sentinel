"""
Trains:
1. A shallow Decision Tree -> exported as plain C if/else code to embed directly
   in the ESP32 firmware (no ML runtime needed on-device, just fast comparisons).
2. A Random Forest -> saved as .joblib, used by the FastAPI backend for the
   more accurate cloud-side classification.

Run: python3 train_models.py
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib

import os
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "sensor_data.csv")
BACKEND_DIR = os.path.join(BASE_DIR, "..", "backend")
FIRMWARE_DIR = os.path.join(BASE_DIR, "..", "esp32_firmware")
os.makedirs(BACKEND_DIR, exist_ok=True)
os.makedirs(FIRMWARE_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)
FEATURES = ["flame_value", "smoke_ppm", "temperature_c", "humidity_pct"]
X = df[FEATURES]
y = df["fire_status"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------- 1. Decision Tree (shallow, for ESP32) ----------
dt = DecisionTreeClassifier(max_depth=4, random_state=42)
dt.fit(X_train, y_train)
dt_pred = dt.predict(X_test)

print("=" * 60)
print("DECISION TREE (on-device, ESP32)")
print("=" * 60)
print(f"Accuracy: {accuracy_score(y_test, dt_pred):.4f}")
print(f"F1 (macro): {f1_score(y_test, dt_pred, average='macro'):.4f}")
print(classification_report(y_test, dt_pred, target_names=["Normal", "Warning", "Fire"]))

joblib.dump(dt, os.path.join(BASE_DIR, "decision_tree.joblib"))
# ---------- 2. Random Forest (backend) ----------
rf = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)

print("=" * 60)
print("RANDOM FOREST (backend, FastAPI)")
print("=" * 60)
print(f"Accuracy: {accuracy_score(y_test, rf_pred):.4f}")
print(f"F1 (macro): {f1_score(y_test, rf_pred, average='macro'):.4f}")
print(classification_report(y_test, rf_pred, target_names=["Normal", "Warning", "Fire"]))

joblib.dump(rf, os.path.join(BACKEND_DIR, "random_forest.joblib"))
print("Feature importances (RF):")
for feat, imp in sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat}: {imp:.3f}")

# ---------- 3. Export Decision Tree as C code for ESP32 ----------
def tree_to_c(tree, feature_names, class_names="ss_status"):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != -2 else "undefined!"
        for i in tree_.feature
    ]
    lines = []
    lines.append("// Auto-generated Decision Tree inference function.")
    lines.append("// Paste this into firesentinel_firmware.ino")
    lines.append("int predictFireStatus(float flame_value, float smoke_ppm, float temperature_c, float humidity_pct) {")

    def recurse(node, depth):
        indent = "  " * (depth + 1)
        if tree_.feature[node] != -2:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            lines.append(f"{indent}if ({name} <= {threshold:.2f}) {{")
            recurse(tree_.children_left[node], depth + 1)
            lines.append(f"{indent}}} else {{")
            recurse(tree_.children_right[node], depth + 1)
            lines.append(f"{indent}}}")
        else:
            value = tree_.value[node][0]
            predicted_class = int(np.argmax(value))
            lines.append(f"{indent}return {predicted_class};  // 0=Normal 1=Warning 2=Fire")

    recurse(0, 0)
    lines.append("}")
    return "\n".join(lines)

c_code = tree_to_c(dt, FEATURES)

with open(os.path.join(FIRMWARE_DIR, "decision_tree.h"), "w") as f:
    f.write(c_code + "\n")

print("\nExported on-device Decision Tree C code -> esp32_firmware/decision_tree.h")