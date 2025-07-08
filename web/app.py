# web/app.py
import streamlit as st
from streamlit_folium import st_folium
import plotly.io as pio
import geopandas as gpd
import folium, json
from folium.plugins import TimestampedGeoJson
from datetime import datetime, timezone
import helpers
import plotly.express as px       
import pandas as pd

# ---------- read & cache data ----------
@st.cache_data
def get_detections():
    return helpers.load_all()                 # loads CSV into a dataframe

det_all = get_detections()
tag_ids  = sorted(det_all.tagname.unique())

# ---------- sidebar ----------
tag  = st.sidebar.selectbox("Choose a tag ID", tag_ids)
fish = det_all[det_all.tagname == tag].copy()
animal = fish.iloc[0]
st.sidebar.markdown(f"**Species:** *{animal.scientificname}* \n**Common:** {animal.commonname}")
st.sidebar.write(f"Detections: {len(fish)}")

# ---------- compute synthesis metrics ----------
fish = helpers.flag_speeds(fish)              # adds speed_ms column
resid = fish.telemetry.residency()            # %
# resid = residency_index(
#             fish,
#             receiver_col="station",
#             time_col="timestamp",
#             station_regex=r"HFX04[6-8]"
#         ) * 100
curve_fig, d50 = fish.telemetry.eff_curve()   # fig + D-50
last_ts = fish.timestamp.max()
if last_ts.tzinfo is None:
    last_ts = last_ts.tz_localize("UTC")
days_old = (datetime.now(timezone.utc) - last_ts).total_seconds() / 86400
hours_old = (datetime.now(timezone.utc) - last_ts).total_seconds() / 3600
outliers = fish[fish.speed_ms > 5]

# ---------- KPI cards ----------
from geopy.distance import geodesic
fish['shift_lat'] = fish.latitude.shift()
fish['shift_lon'] = fish.longitude.shift()

seg_km = fish.apply(
    lambda r: geodesic((r.shift_lat, r.shift_lon),
                       (r.latitude , r.longitude )).km
    if pd.notnull(r.shift_lat) else 0, axis=1
)
track_km   = seg_km.sum()
avg_speed  = fish.speed_ms.mean()          # speed_ms comes from flag_speeds()

# ----- KPI cards (5 across) -----
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Residency %",          f"{resid}")
k2.metric("D-50 (km)",            f"{d50:.2f}")
k3.metric("Last heard (days)",    f"{days_old:.1f}")
k4.metric("Track length (km)",    f"{track_km:.1f}")
k5.metric("Avg speed (m/s)",      f"{avg_speed:.2f}")

# ---------- quick narrative ----------
summary = (
    f"Last ping {hours_old:.1f} h ago at {fish.iloc[-1].station}. "
    f"Residency {resid} %, D-50 {d50:.2f} km. "
    + ("⚠ Speed outliers present." if not outliers.empty else "No QC flags.")
)
st.sidebar.markdown("### Summary")
st.sidebar.markdown(summary)

# ---------- download button ----------
csv_bytes = fish.to_csv(index=False).encode()
st.sidebar.download_button("⬇ Download detections CSV",
                           csv_bytes,
                           file_name=f"{tag}_detections.csv",
                           mime="text/csv")

# ---------- animated track map ----------
st.subheader("Animated track")
gdf = gpd.GeoDataFrame(
    fish, geometry=gpd.points_from_xy(fish.longitude, fish.latitude), crs=4326
)
mp = folium.Map(location=[gdf.geometry.y.mean(), gdf.geometry.x.mean()],
                zoom_start=7)
features = [
    {"type":"Feature",
     "geometry":{"type":"Point","coordinates":[r.longitude, r.latitude]},
     "properties":{"time":r.timestamp.isoformat(),"popup":r.station}}
    for r in gdf.itertuples()
]
TimestampedGeoJson({"type":"FeatureCollection","features":features},
                   period="PT1H", add_last_point=True).add_to(mp)
st_folium(mp, height=500)

# ---------- detection-efficiency curve ----------
st.subheader("Detection-efficiency vs distance")
st.plotly_chart(curve_fig, use_container_width=True)

# ---------- receiver hit distribution ----------
st.subheader("Receiver hit distribution")
hits = (fish.station.value_counts()
                  .sort_values(ascending=True))      # horizontal bar
bar_fig = px.bar(hits,
                 x=hits.values,
                 y=hits.index,
                 orientation="h",
                 height=300,
                 labels={"x": "Detections", "y": "Station"})
st.plotly_chart(bar_fig, use_container_width=True)

# ---------- speed-QC table ----------
if not outliers.empty:
    st.warning(f"⚠ {len(outliers)} detections > 5 m s⁻¹")
    st.dataframe(outliers[["timestamp","station","speed_ms"]])

# ---------- arrival histogram ----------
st.subheader("Arrival-time histogram (all tags)")
hist_fig = det_all.telemetry.arrival_hist()
st.plotly_chart(hist_fig, use_container_width=True)
