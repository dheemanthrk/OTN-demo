import pandas as pd, geopandas as gpd, json
import folium, plotly.express as px
from folium.plugins import TimestampedGeoJson
from geopy.distance import geodesic
from pathlib import Path
import numpy as np

DATA  = Path("data/blue_shark_detections.csv")

# ---------- utilities ----------
@pd.api.extensions.register_dataframe_accessor("telemetry")
class TelemetryAccessor:
    """Adds .residency(), .eff_curve(), .arrival_hist() to any detections DF."""
    def __init__(self, pandas_obj):
        self._df = pandas_obj.sort_values("timestamp")

    def residency(self, line_pattern="HFX"):
        mask = self._df.station.str.contains(line_pattern, case=False)
        return round(mask.mean() * 100, 1)

    def eff_curve(self):
        # pick 'best' receiver by hit count
        best_rx = self._df.station.value_counts().idxmax()
        best_n  = self._df.station.value_counts().max()
        best_lat, best_lon = self._df.loc[self._df.station == best_rx,
                                          ["latitude","longitude"]].iloc[0]
        bins = (self._df.groupby("station")
                        .agg(n=("station","size"),
                             lat=("latitude","first"),
                             lon=("longitude","first"))
                        .reset_index())
        bins["eff"] = bins.n / best_n
        bins["dist_km"] = bins.apply(
            lambda r: geodesic((best_lat,best_lon),(r.lat,r.lon)).km, axis=1)
        bins = bins.sort_values("dist_km")[["dist_km","eff"]]
        d50  = np.interp(0.5, bins.eff[::-1], bins.dist_km[::-1])
        fig  = px.line(bins, x="dist_km", y="eff", markers=True,
                       labels={"dist_km":"Distance (km)","eff":"Efficiency"})
        fig.add_hline(y=0.5, line_dash="dot")
        fig.add_vline(x=d50, line_dash="dot")
        fig.add_annotation(x=d50, y=0.55, text=f"D-50 ≈ {d50:.2f} km",
                           showarrow=False)
        return fig, d50

    def arrival_hist(self, line_pattern="HFX"):
        first = (self._df[self._df.station.str.contains(line_pattern,case=False)]
                 .groupby("tagname", as_index=False).first())
        first["hour"] = first.timestamp.dt.hour
        fig = px.histogram(first, x="hour", nbins=24,
                           labels={"hour":"Hour (UTC)","count":"Tags"})
        return fig
    
import numpy as np
from geopy.distance import geodesic

def flag_speeds(df):
    df = df.sort_values("timestamp").reset_index(drop=True).copy()
    df["speed_ms"] = np.nan
    for i in range(1, len(df)):
        dt = (df.timestamp[i] - df.timestamp[i-1]).total_seconds()
        if dt > 0:
            dist = geodesic((df.latitude[i-1], df.longitude[i-1]),
                            (df.latitude[i]  , df.longitude[i]  )).meters
            df.loc[i, "speed_ms"] = dist / dt
    return df


def load_all():
    det = pd.read_csv(DATA, parse_dates=["datecollected"])
    det.rename(columns={"datecollected":"timestamp"}, inplace=True)
    return det
