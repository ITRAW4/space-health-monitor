import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")
KEY = os.getenv("NASA_API_KEY")
BASE = "https://api.nasa.gov/DONKI/"


def get(endpoint):
    """Download DONKI data in 30-day chunks and combine the results."""
    results = []
    start = date(2025, 1, 1)
    last = date(2025, 12, 31)
    while start <= last:
        end = min(start + timedelta(days=29), last)
        params = {"api_key": KEY, "startDate": start.isoformat(),
                  "endDate": end.isoformat()}
        for _ in range(3):
            try:
                r = requests.get(BASE + endpoint, timeout=60, params=params)
                if r.status_code == 200:
                    results.extend(r.json())
                    break
                print(endpoint, start, "status:", r.status_code, r.text[:150])
            except requests.RequestException as e:
                print(endpoint, start, "failed:", type(e).__name__)
            time.sleep(5)
        start = end + timedelta(days=1)
    return results


def kp_risk(kp):
    """Geomagnetic storm: Kp >= 7 high, Kp >= 5 medium, else low."""
    return "high" if kp >= 7 else "medium" if kp >= 5 else "low"


def speed_risk(speed):
    """CME speed (km/s): >= 1000 high, >= 500 medium, else low."""
    return "high" if speed >= 1000 else "medium" if speed >= 500 else "low"


# Geomagnetic storms (GST)
rows = []
for g in get("GST"):
    kps = [k.get("kpIndex") for k in (g.get("allKpIndex") or [])
           if k.get("kpIndex") is not None]
    if kps:
        rows.append({"time": g.get("startTime"), "max_kp": max(kps),
                     "event_id": g.get("gstID")})
gst = pd.DataFrame(rows, columns=["time", "max_kp", "event_id"])
gst["risk"] = gst["max_kp"].apply(kp_risk)
gst.to_csv(HERE / "gst.csv", index=False)

# Coronal mass ejections (CME)
rows = []
for c in get("CME"):
    analyses = c.get("cmeAnalyses") or []
    best = next((a for a in analyses if a.get("isMostAccurate")),
                analyses[0] if analyses else None)
    speed = best.get("speed") if best else None
    if speed is not None:
        rows.append({"time": c.get("startTime"), "speed_km_s": speed,
                     "event_id": c.get("activityID")})
cme = pd.DataFrame(rows, columns=["time", "speed_km_s", "event_id"])
cme["risk"] = cme["speed_km_s"].apply(speed_risk)
cme.to_csv(HERE / "cme.csv", index=False)

print("GST events:", len(gst))
print(gst["risk"].value_counts())
print("CME events:", len(cme))
print(cme["risk"].value_counts())