from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
rng = np.random.default_rng(42)
POINTS = {"low": 1, "medium": 3, "high": 8}
N_SENSORS = 8

# Real NASA DONKI events -> daily severity (0-8)
frames = []
for name in ("gst.csv", "cme.csv"):
    df = pd.read_csv(HERE / name)
    df["day"] = pd.to_datetime(df["time"], utc=True, errors="coerce").dt.floor("D")
    df["points"] = df["risk"].map(POINTS)
    frames.append(df[["day", "points"]])
events = pd.concat(frames).groupby("day")["points"].max()

days = pd.date_range("2025-01-01", "2025-12-31", freq="D", tz="UTC")
severity = events.reindex(days).fillna(0)

# SIMULATED sensor readings driven by the real severity
rows = []
for day, sev in severity.items():
    rad_values = []
    for i in range(N_SENSORS):
        sid = f"dust-{i + 1:02d}"
        rad = max(10 + sev * 6 + rng.normal(0, 2), 0)
        rad_values.append(rad)
        rows.append((day, sid, "radiation_index", round(rad, 1), "index"))
        rows.append((day, sid, "temperature", round(22 + rng.normal(0, 0.6), 1), "C"))
        rows.append((day, sid, "humidity", round(45 + rng.normal(0, 3), 1), "%"))
    stress = 20 + 0.6 * float(np.mean(rad_values)) + rng.normal(0, 2)
    rows.append((day, "crew-01", "crew_stress_index", round(stress, 1), "index"))

out = pd.DataFrame(rows, columns=["time", "sensor_id", "type", "value", "unit"])
out.to_csv(HERE / "sensors.csv", index=False)
print("Simulated readings:", len(out))