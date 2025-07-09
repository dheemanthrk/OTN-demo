# OTN Programmer — Demo Dashboard

**Interactive visualisation + synthesis of acoustic-telemetry detections**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-streamlit-url.streamlit.app)

---

## What the dashboard delivers

| Section                        | Why it matters                                                                                            |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **KPI cards**                  | Instant synthesis → **Residency % · D-50 (km) · Last-heard (days) · Track-length (km) · Avg-speed (m/s)** |
| **Animated track map**         | Folium map with a time-slider **plus** a polyline of the full trajectory                                  |
| **Detection-efficiency curve** | Plotly line with vertical D-50 marker (receiver performance)                                              |
| **Receiver-hit bar chart**     | Shows which stations logged the tag most often                                                            |
| **Arrival-time histogram**     | When all fish crossed the Halifax Line                                                                    |
| **QC outlier table**           | Flags detections implying > 5 m s⁻¹ swim speed                                                            |
| **CSV download + narrative**   | One-click export of the filtered detections and a plain-English summary                                   |

Everything updates live when you pick a different **tag ID** in the sidebar.

---

## Quick start 🚀

```bash
# clone and enter
git clone https://github.com/yourname/otn-demo.git
cd otn-demo

# install deps
pip install -r requirements.txt        # uses only PyPI wheels

# run
streamlit run web/app.py
```

> **Live demo** (hosted on Streamlit Cloud – just open in a browser)
> [https://your-streamlit-url.streamlit.app](https://your-streamlit-url.streamlit.app)

---

## Repo layout

```
otn-demo/
├── data/                 sample_detections.csv, sample_receivers.csv
├── helpers.py            flag_speeds(), load_all(), efficiency helpers
├── web/
│   └── app.py            Streamlit dashboard
├── requirements.txt
└── README.md             (this file)
```

---

## How the metrics are computed

| Metric           | Method                                                                                                                                  |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Residency %**  | `len(core_hits) / len(all_hits) * 100`, where core = `HFX046–HFX048` (1-liner easily swappable for `resonATe.metrics.residency_index`). |
| **D-50**         | Bin detections by distance, derive detection-efficiency, linearly interpolate 50 % crossing.                                            |
| **Track length** | Sum great-circle distances between consecutive detections (`geopy.geodesic`).                                                           |
| **Avg speed**    | Mean of segment speeds = distance/Δt; rows > 5 m s⁻¹ highlighted.                                                                       |

All heavy calculations are wrapped in `@st.cache_data`, so changing tags is instant.

---

## Dependencies

```
streamlit
streamlit-folium
folium
geopandas
pandas
plotly
geopy
shapely
```

*(Optional)*

```bash
pip install git+https://gitlab.oceantrack.org/otndc/resonate.git
```

lets you swap helper functions for OTN’s official **`resonATe`** toolkit.

---


### Potential next steps

* Swap CSV demo for full **Detection-Extract Parquet** reader.
* Plug in `resonATe` QC suite (impossible-velocity, clock-drift).
* Add FastAPI `/metrics` endpoint for Grafana ingestion.
* Bundle daily **PDF reports** via `weasyprint`.

---

Made by **Dheemanth Kumawat**
