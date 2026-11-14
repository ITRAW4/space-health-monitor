# Space Health Monitor

NASA Space Apps Challenge 2026 - Saudi Arabia

A dashboard that links space weather events (NASA DONKI) to astronaut health risk,
with early-warning alerts and a simulated "smart dust" sensor swarm concept.

## Data
- NASA DONKI API: geomagnetic storms (GST) and coronal mass ejections (CME), 2025
- NASA Human Research Program (HRP): hazards and risks pages
- NASA OCHMO radiation protection brief (NASA-STD-3001 Vol. 1): radiation limits
- Data sheets prepared by our data analysts
- HRP hazards table: compiled by the team from NASA HRP pages (nasa.gov/hrp/hazards, nasa.gov/hrp/risks)

## Simulated parts (honest note)
- Astronaut exposure index and crew stress index are simulated, not real measurements.
- The smart dust swarm is a futuristic concept, simulated from real space weather events.
- Risk thresholds (Kp, CME speed) are defined by our team.

## Run
1. Put your NASA API key in a `.env` file: `NASA_API_KEY=your_key`
2. `pip install -r requirements.txt`
3. `python fetch_data.py`
4. `python sensors.py`
5. `streamlit run app.py`

## Use of AI
We used an AI assistant (Claude) to help write and debug the code. The team defined
the idea, the risk rules, and reviewed the data and sources.