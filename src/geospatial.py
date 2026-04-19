"""
geospatial.py — Spatial joins and distance calculations.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from src.utils import save_csv, ensure_dirs

PROCESSED = Path("data/processed")
METRIC_CRS = "EPSG:32718"
WGS84_CRS  = "EPSG:4326"


def points_to_geodataframe(df, lat_col="latitud", lon_col="longitud", crs=WGS84_CRS):
    """Convert a DataFrame with lat/lon columns to a GeoDataFrame."""
    df = df.dropna(subset=[lat_col, lon_col]).copy()
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs=crs,
    )


def spatial_join_to_districts(points_gdf, districts_gdf, point_label="points"):
    """Assign each point to a district via spatial join."""
    pts  = points_gdf.to_crs(WGS84_CRS)
    dist = districts_gdf.to_crs(WGS84_CRS)
    joined = gpd.sjoin(pts, dist[["ubigeo", "geometry"]], how="left", predicate="within")
    joined = joined.drop(columns=["index_right"], errors="ignore")
    
    ubigeo_col = "ubigeo_left" if "ubigeo_left" in joined.columns else "ubigeo"
    if "ubigeo_left" in joined.columns:
        joined = joined.rename(columns={"ubigeo_left": "ubigeo"})
        joined = joined.drop(columns=["ubigeo_right"], errors="ignore")
    
    print(f"  [SpatialJoin] {point_label}: {len(joined)} points, {joined['ubigeo'].isna().sum()} unmatched.")
    return joined


def compute_nearest_facility_distance(centers_gdf, facilities_gdf):
    """Compute distance (km) from each populated center to its nearest facility.

    Uses EPSG:32718 (UTM Zone 18S) — a metric CRS covering Peru —
    so distances are in meters, then converted to kilometers.
    """
    centers_m    = centers_gdf.to_crs(METRIC_CRS).copy()
    facilities_m = facilities_gdf.to_crs(METRIC_CRS).copy()
    nearest_idx  = facilities_m.geometry.sindex.nearest(centers_m.geometry, return_all=False)
    nearest_geom = facilities_m.geometry.iloc[nearest_idx].values
    centers_m["dist_nearest_km"] = [
        c.distance(n) / 1000 for c, n in zip(centers_m.geometry, nearest_geom)
    ]
    result = centers_gdf.copy()
    result["dist_nearest_km"] = centers_m["dist_nearest_km"].values
    return result


def build_geospatial_layers(pop_centers, ipress, districts):
    """Full geospatial pipeline."""
    print("\n[GEO] Building GeoDataFrames...")
    ipress_gdf      = points_to_geodataframe(ipress)
    pop_centers_gdf = points_to_geodataframe(pop_centers)

    print("\n[GEO] Assigning facilities to districts...")
    ipress_gdf = spatial_join_to_districts(ipress_gdf, districts, "IPRESS Facilities")

    print("\n[GEO] Assigning populated centers to districts...")
    pop_centers_gdf = spatial_join_to_districts(pop_centers_gdf, districts, "Populated Centers")

    print("\n[GEO] Computing distance to nearest facility...")
    pop_centers_gdf = compute_nearest_facility_distance(pop_centers_gdf, ipress_gdf)

    ensure_dirs(PROCESSED)
    save_csv(pop_centers_gdf.drop(columns="geometry"), PROCESSED / "pop_centers_geo.csv")
    save_csv(ipress_gdf.drop(columns="geometry"),      PROCESSED / "ipress_geo.csv")

    return pop_centers_gdf, ipress_gdf