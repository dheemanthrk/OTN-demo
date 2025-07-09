# web/app.py  –  OTN demo dashboard
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import TimestampedGeoJson
from datetime import datetime, timezone
from geopy.distance import geodesic
import plotly.express as px
import helpers
import base64, pathlib

# --- title with logo -------------------------------------------------
import base64, pathlib
logo_path = pathlib.Path(__file__).parent / "static" / "Ocean_Tracking_Network.png"
logo_b64  = base64.b64encode(logo_path.read_bytes()).decode()


# ──  UI THEME & PAGE SETUP  ─────────────────────────────────────────────
st.set_page_config(
    page_title="OTN Telemetry Snapshot",
    page_icon="🐟",
    layout="wide"
)

st.markdown(
    """
    <style>
    .css-1v0mbdj {padding-top: 0rem;}           /* tighten top padding */
    .divider {height:6px; background:
        linear-gradient(90deg,#008cba 0%,#5ab7e5 50%,#008cba 100%);
        border-radius:3px; margin:0.4rem 0 1rem 0;}
    .stApp {background: linear-gradient(#F2FAFF 0%, #D7EFFA 40%, #B8E5F4 100%);}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
      html { zoom: 1 !important; }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    f"""
<div style="display:flex; align-items:center; gap:0.6rem;
            font-size:1.8rem; font-weight:600; line-height:1.2;">
  <img src="data:image/png;base64,{logo_b64}" style="height:48px;">
  OTN&nbsp;Programmer&nbsp;Demo&nbsp;—&nbsp;Movement&nbsp;&amp;&nbsp;Infrastructure&nbsp;Snapshot
</div>
""",
    unsafe_allow_html=True
)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ──  DATA LOAD (cached)  ────────────────────────────────────────────────
@st.cache_data
def get_detections():
    return helpers.load_all()          # sample_detections & receivers

det_all = get_detections()
tag_ids  = sorted(det_all.tagname.unique())

# ──  SIDEBAR  ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    mode = st.radio("Mode", ["Single tag", "Compare tags"], horizontal=True)

    if mode == "Single tag":
        tags_selected = [st.selectbox("Choose a tag ID", tag_ids)]
    else:
        tags_selected = st.multiselect(
            "Choose tag IDs (max 10)", tag_ids, default=tag_ids[:3],
            max_selections=10
        )
    show_story = st.checkbox("📢 Story mode (fun outreach blurb)")

    st.markdown("##### Having trouble?")
    st.caption("If the map or charts glitch, hit **⟳ Reload**. and pick another tag ID. The data size is small so it caches quickly.")
    st.caption("🔍 If the page appears oversized, hit **Ctrl + -** (Cmd + - on Mac) to 80%.")

    st.markdown("#### Guide")
    st.markdown(
        """
        * **Tag ID** – unique code transmitted by one fish.<br>
        * **Residency %** – share of detections on Halifax Line.<br>
        * **D-50** – distance where receivers hear 50 % of pings.<br>
        * **Track km** – cumulative great-circle path.<br>
        * **Avg speed** – mean swim speed between detections.<br>
        """,
        unsafe_allow_html=True
    )

# ──  PER-TAG METRIC HELPERS  ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_metrics(tag: str, det_all: pd.DataFrame):
    fish = det_all[det_all.tagname == tag].copy()
    fish = helpers.flag_speeds(fish)

    resid          = fish.telemetry.residency()
    curve_fig, d50 = fish.telemetry.eff_curve()

    last_ts = pd.to_datetime(fish.timestamp.max(), utc=True)
    days_old = (datetime.now(timezone.utc) - last_ts).total_seconds() / 86400
    hours_old = days_old * 24

    fish["shift_lat"] = fish.latitude.shift()
    fish["shift_lon"] = fish.longitude.shift()
    track_km = (
        fish.apply(
            lambda r: geodesic((r.shift_lat, r.shift_lon),
                               (r.latitude, r.longitude)).km
            if pd.notnull(r.shift_lat) else 0,
            axis=1
        ).sum()
    )
    avg_speed = fish.speed_ms.mean()
    hits      = fish.station.value_counts().sort_values(ascending=True)
    outliers  = fish[fish.speed_ms > 5]

    return (fish, resid, d50, days_old, hours_old,
            track_km, avg_speed, curve_fig, hits, outliers)

@st.cache_data(show_spinner=False)
def batch_metrics(tags, det_all):
    rows = []
    for tg in tags:
        _, resid, d50, *_ , track_km, __, ___, hits, ____ = compute_metrics(tg, det_all)
        rows.append(dict(tag=tg, resid=resid, d50=d50,
                         track_km=track_km, hits_total=hits.sum()))
    return pd.DataFrame(rows)

# ──  UI BRANCH  ─────────────────────────────────────────────────────────
if len(tags_selected) == 1:
    # ========== SINGLE-TAG VIEW ========================================
    tag = tags_selected[0]
    (fish, resid, d50, days_old, hours_old,
     track_km, avg_speed, curve_fig, hits, outliers) = compute_metrics(tag, det_all)

    # species / counts in sidebar
    animal = fish.iloc[0]
    st.sidebar.markdown(f"**Species:** *{animal.scientificname}*  \n"
                        f"**Common:** {animal.commonname}")
    st.sidebar.write(f"Detections: {len(fish)}")

    # KPI cards
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Residency %",        f"{resid:.1f}")
    k2.metric("D-50 (km)",          f"{d50:.2f}")
    k3.metric("Last heard (days)",  f"{days_old:.1f}")
    k4.metric("Track length (km)",  f"{track_km:.1f}")
    k5.metric("Avg speed (m/s)",    f"{avg_speed:.2f}")

    if show_story:
        # choose a 24-h window around the first detection
        start = fish.timestamp.min().floor("H")
        end   = start + pd.Timedelta("24H")
        day_df = fish[(fish.timestamp >= start) & (fish.timestamp < end)]

        km_travel = (
            day_df
            .assign(lat_shift=day_df.latitude.shift(),
                    lon_shift=day_df.longitude.shift())
            .apply(lambda r: geodesic((r.lat_shift, r.lon_shift),
                                    (r.latitude, r.longitude)).km
                if pd.notnull(r.lat_shift) else 0, axis=1).sum()
        )

        first_sta = day_df.iloc[0].station
        last_sta  = day_df.iloc[-1].station
        detections = len(day_df)

        st.markdown(
            f"""
            ### 🦈 Meet *{animal.commonname.title()}*  
            On **{start.date()}**, this shark covered **{km_travel:.1f} km**  
            moving from **{first_sta}** to **{last_sta}** and pinged
            our receivers **{detections} times!**

            > “That’s like swimming the length of {km_travel/2:.0f} Olympic pools
            in a single night!” 🌊🏊‍♂️
            """,
            unsafe_allow_html=True
        )


    # narrative
    st.sidebar.markdown("### Summary")
    st.sidebar.markdown(
        f"Last ping {hours_old:.1f} h ago at {fish.iloc[-1].station}.  "
        f"Residency {resid:.1f} %, D-50 {d50:.2f} km. "
        + ("⚠ Speed outliers present." if not outliers.empty else "No QC flags.")
    )

    # CSV download
    st.sidebar.download_button("⬇ Download detections CSV",
                               fish.to_csv(index=False).encode(),
                               f"{tag}.csv", "text/csv")

    # ---------- map ----------
    # st.subheader("Animated track")
    # gdf  = gpd.GeoDataFrame(fish,
    #        geometry=gpd.points_from_xy(fish.longitude, fish.latitude), crs=4326)
    # mp   = folium.Map(location=[gdf.geometry.y.mean(), gdf.geometry.x.mean()],
    #                   zoom_start=7, scrollWheelZoom=False)
    # feats = [{"type":"Feature",
    #           "geometry":{"type":"Point","coordinates":[r.longitude,r.latitude]},
    #           "properties":{"time":r.timestamp.isoformat(),"popup":r.station}}
    #          for r in gdf.itertuples()]
    # TimestampedGeoJson({"type":"FeatureCollection","features":feats},
    #                    period="PT1H", duration="P1D",
    #                    add_last_point=True).add_to(mp)
    # st_folium(mp, height=500, width="50", key=f"map-{tag}")
    # ---------- map ----------
    st.subheader("Animated track")

    # Build Folium map (wheel-zoom OFF)
    gdf = gpd.GeoDataFrame(
        fish,
        geometry=gpd.points_from_xy(fish.longitude, fish.latitude), crs=4326
    )
    mp = folium.Map(
        location=[gdf.geometry.y.mean(), gdf.geometry.x.mean()],
        zoom_start=7,
        scrollWheelZoom=False          # ← stops accidental zoom while scrolling
    )

    feats = [
        {"type": "Feature",
        "geometry": {"type": "Point",
                    "coordinates": [r.longitude, r.latitude]},
        "properties": {"time": r.timestamp.isoformat(),
                        "popup": r.station}}
        for r in gdf.itertuples()
    ]
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": feats},
        period="PT1H",
        add_last_point=True
    ).add_to(mp)

    # Centre the map in the layout
    # left, mid, right = st.columns([1, 8, 1])     # 8-wide map, 1-wide gutters
    # with mid:
    st_folium(
            mp,
            height=500,        # postcard height
            width="100%",      # fills the middle column
            key=f"map-{tag}"
    )

    # curve
    st.subheader("Detection-efficiency vs distance")
    st.plotly_chart(curve_fig, use_container_width=True, key=f"curve-{tag}")

    # hits bar
    st.subheader("Receiver hit distribution")
    bar = px.bar(hits, x=hits.values, y=hits.index,
                 orientation="h", height=300,
                 labels={"x":"Detections","y":"Station"})
    st.plotly_chart(bar, use_container_width=True)

    # QC table
    if not outliers.empty:
        st.warning(f"⚠ {len(outliers)} detections > 5 m s⁻¹")
        st.dataframe(outliers[["timestamp","station","speed_ms"]])

else:
    # ========== COMPARE-TAGS VIEW ======================================
    comp = batch_metrics(tags_selected, det_all)

    st.subheader("Comparison table")
    st.dataframe(
        comp.set_index("tag")
            .style.format({"resid":"{:.1f}",
                           "d50":"{:.2f}",
                           "track_km":"{:.1f}"})
    )

    st.subheader("Residency % by tag")
    bar = px.bar(comp, x="tag", y="resid",
                 labels={"resid":"Residency %","tag":"Tag ID"},
                 height=350, text_auto=".1f")
    st.plotly_chart(bar, use_container_width=True)

    st.subheader("Tracks overlay")
    colours = px.colors.qualitative.Safe
    # build map centred on the tracks’ bounding box
    all_lat = pd.concat([compute_metrics(t, det_all)[0].latitude for t in tags_selected])
    all_lon = pd.concat([compute_metrics(t, det_all)[0].longitude for t in tags_selected])

    bounds = [[all_lat.min(), all_lon.min()],
            [all_lat.max(), all_lon.max()]]

    mcmp = folium.Map()                 # let Folium pick a default
    mcmp.fit_bounds(bounds, padding=(20, 20))
    for i, tg in enumerate(tags_selected):
        fish, *_ = compute_metrics(tg, det_all)
        gdf = gpd.GeoDataFrame(fish,
               geometry=gpd.points_from_xy(fish.longitude, fish.latitude), crs=4326)
        folium.PolyLine(
            list(zip(gdf.geometry.y, gdf.geometry.x)),
            color=colours[i % len(colours)], weight=3, opacity=0.7,
            tooltip=tg
        ).add_to(mcmp)
    st_folium(mcmp, height=500, width="100%", key=f"cmp-{','.join(tags_selected)}")

    st.info("Detailed QC table and CSV download are available in **Single tag** mode.")

# ──  ARRIVAL HISTOGRAM (always show)  ──────────────────────────────────
st.subheader("Arrival-time histogram (all tags)")
hist_fig = det_all.telemetry.arrival_hist()
st.plotly_chart(hist_fig, use_container_width=True)

# ──  FOOTER  ───────────────────────────────────────────────────────────
st.markdown("---  \n© 2025 Ocean Tracking Network demo • Code on "
            "[GitHub](https://github.com/dheemanthrk/otn-demo)")
