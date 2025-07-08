# OTN Programmer — Demo Dashboard

Interactive visualisation + synthesis of acoustic-telemetry detections
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-streamlit-url.streamlit.app)

---

## What this dashboard shows 📊

| Section                        | Purpose                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **KPI cards**                  | Instant synthesis: **Residency % · D-50 (km) · Last-heard (days) · Track-length (km) · Avg-speed (m/s)** |
| **Animated track map**         | Folium map with time-slider **and** a polyline of the full trajectory                                    |
| **Detection-efficiency curve** | Plotly line, vertical D-50 marker                                                                        |
| **Receiver-hit bar chart**     | Which stations logged the tag most often                                                                 |
| **Arrival-time histogram**     | When all fish crossed the Halifax Line                                                                   |
| **QC outlier table**           | Flags detections implying > 5 m s⁻¹ swim speed                                                           |
| **CSV & narrative in sidebar** | One-click data export + plain-English summary                                                            |

Everything updates as you pick different `tagname`s in the sidebar.

---

## Quick start 🚀

```bash
# 1. clone and enter
git clone https://github.com/yourname/otn-demo.git
cd otn-demo

# 2. install
pip install -r requirements.txt

# 3. run
streamlit run web/app.py
```

````

> **Live demo:** [https://your-streamlit-url.streamlit.app](https://your-streamlit-url.streamlit.app) > _(Hosted on Streamlit Cloud — opens in any browser, no installs.)_

---

## Repo layout

```
otn-demo/
├─ data/          sample_detections.csv, sample_receivers.csv
├─ helpers.py     flag_speeds(), load_all(), efficiency helpers
├─ web/app.py     Streamlit dashboard
├─ requirements.txt
└─ README.md
```

---

## How the metrics are calculated 🔍

| Metric           | Method                                                                                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Residency %**  | For Halifax core receivers (`HFX046–HFX048`). `len(core_hits) / len(all_hits) * 100`. (One-liner can be swapped for `resonATe.metrics.residency_index`.) |
| **D-50**         | Bin detections by distance-to-receiver, compute detection-efficiency, interpolate 50 % crossing.                                                         |
| **Track length** | Sum great-circle distances between consecutive detections (`geopy.geodesic`).                                                                            |
| **Avg speed**    | Mean of segment speeds (`distance / Δt`) — outliers flagged if > 5 m s⁻¹.                                                                                |

All heavy ops are cached in `@st.cache_data`, so switching tags is instant.

---

## Dependencies

`streamlit • streamlit-folium • folium • geopandas • pandas • plotly • geopy • shapely`

_(Optional)_

```bash
pip install git+https://gitlab.oceantrack.org/otndc/resonate.git
```

lets you replace helper functions with OTN’s own `resonATe` library.

---

## Screenshot

> ![dashboard screenshot](docs/screenshot.png) > _(Static image for e-mail clients that block live links.)_

---

### Next steps if this were production

- Swap CSV loaders for direct **Detection-Extract** Parquet reader.
- Plug in `resonATe` QC suite (impossible-velocity, clock-drift).
- Add a FastAPI `/metrics` endpoint for Grafana ingestion.
- Bundle daily **PDF report** via `weasyprint`.

---

Made by **Dheemanth Kumawat** for the OTN Programmer interview, July 2025.
````
