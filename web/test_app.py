import json, streamlit as st, plotly.io as pio
from streamlit_folium import st_folium
import folium, pathlib

FIGS   = pathlib.Path("figs")
TAG    = "A69-9001-24395"        # or read the tag list dynamically

st.set_page_config("OTN Demo", layout="wide")
st.title("OTN Programmer Demo – Movement & Infrastructure Snapshot")

# ---------- map ----------
st.subheader("Animated track")
html = (FIGS / f"track_map_{TAG}.html").read_text()
st.components.v1.html(html, height=500, scrolling=False)

# ---------- efficiency curve ----------
st.subheader("Detection-efficiency vs distance")
curve_json = json.loads((FIGS / f"eff_curve_{TAG}.json").read_text())
st.plotly_chart(pio.from_json(json.dumps(curve_json)),
                use_container_width=True)

# ---------- arrival histogram ----------
st.subheader("First-arrival times at Halifax Line")
hist_html = (FIGS / "arrival_histogram.html").read_text()
st.components.v1.html(hist_html, height=400, scrolling=False)
