from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

HERE = Path(__file__).parent
st.set_page_config(page_title="Space Health Monitor", layout="wide")
st.title("Space Health Monitor")

if not (HERE / "gst.csv").exists() or not (HERE / "cme.csv").exists():
    st.warning("Run fetch_data.py first to download NASA DONKI data.")
    st.stop()

gst = pd.read_csv(HERE / "gst.csv")
cme = pd.read_csv(HERE / "cme.csv")
for d in (gst, cme):
    d["time"] = pd.to_datetime(d["time"], errors="coerce", utc=True)
gst = gst.sort_values("time")
cme = cme.sort_values("time")

# 1) Space environment status
st.header("1) Space environment status (NASA DONKI)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Geomagnetic storms", len(gst))
c2.metric("CME events", len(cme))
c3.metric("Highest Kp", float(gst["max_kp"].max()) if len(gst) else 0)
c4.metric("Fastest CME (km/s)", int(cme["speed_km_s"].max()) if len(cme) else 0)

left, right = st.columns(2)
left.plotly_chart(px.scatter(gst, x="time", y="max_kp", color="risk",
                  title="Geomagnetic storms (Kp index)"),
                  use_container_width=True)
right.plotly_chart(px.scatter(cme, x="time", y="speed_km_s", color="risk",
                   title="Coronal mass ejections (speed, km/s)"),
                   use_container_width=True)

# Combine events for the astronaut index and alerts
events = pd.concat([
    gst.assign(type="Geomagnetic storm",
               detail=gst["max_kp"].map(lambda v: f"Kp {v}")),
    cme.assign(type="CME", detail=cme["speed_km_s"].map(lambda v: f"{v:.0f} km/s")),
])[["time", "type", "detail", "risk"]].sort_values("time")

# 2) Astronaut status (simulation)
st.header("2) Astronaut status (simulation based on NASA HRP research)")
points = {"low": 1, "medium": 3, "high": 8}
dose = int(events["risk"].map(points).tail(10).sum())
st.progress(min(dose / 40, 1.0))
st.caption(f"Radiation exposure index (simulated, last 10 events): {dose}")
st.subheader("NASA radiation limits (reference)")
lim = pd.read_csv(HERE / "radiation_limits.csv")
for col, (_, r) in zip(st.columns(len(lim)), lim.iterrows()):
    col.metric(r["Parameter / Metric"], f'{r["Measured value"]} {r["Unit"]}')
st.caption("Source: NASA OCHMO radiation protection technical brief "
           "(NASA-STD-3001 Vol. 1). Data sheet prepared by our data analyst Dalal and Amna. "
           "Our exposure index above is relative, not in mSv.")

# 3) Alerts
st.header("3) Early-warning alerts")
for _, row in events[events["risk"] != "low"].tail(6).iterrows():
    msg = f"{row['type']} ({row['detail']}) on {row['time']:%Y-%m-%d %H:%M}: {row['risk']} risk"
    (st.error if row["risk"] == "high" else st.warning)(msg)
    hrp_path = HERE / "hrp_table.csv"
if hrp_path.exists():
    hrp = pd.read_csv(hrp_path, sep=None, engine="python")
    match = hrp[hrp.iloc[:, 0].str.contains("radiation", case=False, na=False)]
    if len(match):
        st.info("Potential effect on the astronaut (NASA HRP, space radiation): "
                f"{match.iloc[0, 1]}")
        st.caption(f"Source: {match.iloc[0, 3]}. Linking space-weather events "
                   "to the radiation hazard is the team's assumption.")
# 4) Smart dust swarm (simulated concept)
st.header("4) Smart dust swarm (simulated concept, not real sensors)")
sensors_path = HERE / "sensors.csv"
if sensors_path.exists():
    s = pd.read_csv(sensors_path)
    s["time"] = pd.to_datetime(s["time"], utc=True)
    rad = s[s["type"] == "radiation_index"].groupby("time")["value"].mean().reset_index()
    st.plotly_chart(
        px.line(rad, x="time", y="value", title="Swarm average radiation index (simulated)"),
        use_container_width=True,
    )
    last_day = s["time"].max()
    dust = s[(s["time"] == last_day) & (s["sensor_id"].str.startswith("dust"))]
    st.dataframe(dust.pivot_table(index="sensor_id", columns="type", values="value"))
    crew = s[(s["time"] == last_day) & (s["type"] == "crew_stress_index")]["value"].iloc[0]
    st.metric("Crew stress index (simulated)", f"{crew:.1f}")
    if rad["value"].iloc[-1] > 50:
        st.error("Swarm alert: radiation index above threshold")
else:
    st.info("Run sensors.py to generate the simulated swarm data.")
st.caption("Risk thresholds are simple team-defined rules. "
           "The astronaut index is a simulation, not real astronaut data.")
import numpy as np
import plotly.graph_objects as go

st.header("5) Orbital pollution and astronaut vitals (simulated)")
level = st.slider("Orbital pollution level (simulated)", 0, 8, 3)

# Earth + pollution dots around it
rng = np.random.default_rng(7)
N = 1400
r = rng.uniform(1.15, 1.9, N)
theta = rng.uniform(0, 2 * np.pi, N)
phi = np.arccos(rng.uniform(-1, 1, N))
x = r * np.sin(phi) * np.cos(theta)
y = r * np.sin(phi) * np.sin(theta)
z = r * np.cos(phi)
n = 100 + level * 150

u, v = np.mgrid[0:2 * np.pi:60j, 0:np.pi:30j]
earth = go.Figure()
earth.add_trace(go.Surface(x=np.cos(u) * np.sin(v), y=np.sin(u) * np.sin(v), z=np.cos(v),
                           colorscale="Blues", showscale=False, hoverinfo="skip"))
earth.add_trace(go.Scatter3d(x=x[:n], y=y[:n], z=z[:n], mode="markers",
                             marker=dict(size=2, color="red", opacity=0.8),
                             name="pollution"))
earth.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0),
                    scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False))
st.plotly_chart(earth, width="stretch")

# Astronaut vitals driven by the pollution level (simulated)
hr = 65 + 4 * level
spo2 = round(98 - 0.4 * level, 1)
stress = 20 + 6 * level
dose = 10 + 6 * level

st.subheader("Astronaut vitals (simulated)")
a, b, c, d = st.columns(4)
a.metric("Heart rate", f"{hr} bpm", f"{hr - 65:+d}", delta_color="inverse")
b.metric("Blood oxygen (SpO2)", f"{spo2}%", f"{spo2 - 98:+.1f}")
c.metric("Stress index", stress, f"{stress - 20:+d}", delta_color="inverse")
d.metric("Radiation exposure index", dose, f"{dose - 10:+d}", delta_color="inverse")

if level >= 6:
    st.error("High pollution: crew should move to the shielded area.")
elif level >= 4:
    st.warning("Elevated pollution: monitor crew vitals closely.")

st.caption("Simulation: dots and vitals are illustrative, not real measurements. "
           "The link between pollution level and vitals is a team assumption.")