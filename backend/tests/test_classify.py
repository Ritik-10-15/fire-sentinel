"""
Unit tests for the classify() function in main.py — the core piece of logic
that turns a sensor reading into a Fire/Warning/Normal prediction.

Run from the backend/ folder with:
    pytest tests/ -v
"""

import sys
import os

# Let this test file import main.py, which lives one folder up
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import classify


def test_clear_fire_case():
    """Low flame reading + high smoke + high temp + low humidity should be Fire."""
    reading = {
        "flame_value": 300,
        "smoke_ppm": 3500,
        "temperature_c": 80,
        "humidity_pct": 15,
    }
    result = classify(reading)
    assert result["status_label"] == "Fire"
    assert result["confidence"] > 0.8


def test_clear_normal_case():
    """High flame reading (no flame detected) + low smoke + room temp should be Normal."""
    reading = {
        "flame_value": 3900,
        "smoke_ppm": 100,
        "temperature_c": 22,
        "humidity_pct": 55,
    }
    result = classify(reading)
    assert result["status_label"] == "Normal"
    assert result["confidence"] > 0.8


def test_clear_warning_case():
    """Moderate smoke + elevated temp, no confirmed flame, should be Warning."""
    reading = {
        "flame_value": 2400,
        "smoke_ppm": 700,
        "temperature_c": 35,
        "humidity_pct": 40,
    }
    result = classify(reading)
    assert result["status_label"] == "Warning"


def test_confidence_is_valid_probability():
    """Confidence should always be a number between 0 and 1, never outside that range."""
    reading = {
        "flame_value": 1000,
        "smoke_ppm": 1500,
        "temperature_c": 50,
        "humidity_pct": 25,
    }
    result = classify(reading)
    assert 0.0 <= result["confidence"] <= 1.0


def test_status_code_matches_label():
    """The numeric status_code should always correspond to the correct label."""
    reading = {"flame_value": 300, "smoke_ppm": 3500, "temperature_c": 80, "humidity_pct": 15}
    result = classify(reading)

    expected_labels = {0: "Normal", 1: "Warning", 2: "Fire"}
    assert result["status_label"] == expected_labels[result["status_code"]]


def test_extreme_fire_values_still_classify():
    """Sanity check: very extreme values shouldn't crash the model, and should still read as Fire."""
    reading = {
        "flame_value": 0,
        "smoke_ppm": 9000,
        "temperature_c": 120,
        "humidity_pct": 3,
    }
    result = classify(reading)
    assert result["status_label"] == "Fire"


def test_extreme_normal_values_still_classify():
    """Sanity check: maximum flame reading (definitely no flame) with minimal smoke should be Normal."""
    reading = {
        "flame_value": 4095,
        "smoke_ppm": 0,
        "temperature_c": 20,
        "humidity_pct": 60,
    }
    result = classify(reading)
    assert result["status_label"] == "Normal"
    