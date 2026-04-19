"""
cleaning.py — Data cleaning and preprocessing for all four datasets.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from src.utils import standardize_columns, log_summary, save_csv, ensure_dirs

PROCESSED = Path("data/processed")

LAT_MIN, LAT_MAX = -18.5, -0.0
LON_MIN, LON_MAX = -81.5, -68.5


def _valid_coords(df, lat_col, lon_col):
    """Remove rows with coordinates outside Peru's bounding box."""
    df = df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    mask = (
        df[lat_col].between(LAT_MIN, LAT_MAX)
        & df[lon_col].between(LON_MIN, LON_MAX)
    )
    print(f"  [Coords] Dropped {(~mask).sum()} rows with invalid coordinates.")
    return df[mask].reset_index(drop=True)


def clean_populated_centers(df):
    df = standardize_columns(df)
    df = df.drop_duplicates()
    lat_col = next((c for c in df.columns if "lat" in c), None)
    lon_col = next((c for c in df.columns if "lon" in c or "lng" in c), None)
    if lat_col and lon_col:
        df = _valid_coords(df, lat_col, lon_col)
        df = df.rename(columns={lat_col: "latitud", lon_col: "longitud"})
    if "ubigeo" in df.columns:
        df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)
    if "poblacion" in df.columns:
        df["poblacion"] = pd.to_numeric(df["poblacion"], errors="coerce").fillna(0).astype(int)
    log_summary(df, "Populated Centers (clean)")
    ensure_dirs(PROCESSED)
    save_csv(df, PROCESSED / "centros_poblados_clean.csv")
    return df


def clean_ipress_facilities(df):
    df = standardize_columns(df)
    df = df.drop_duplicates()
    lat_col = next((c for c in df.columns if "lat" in c), None)
    lon_col = next((c for c in df.columns if "lon" in c or "lng" in c), None)
    if lat_col and lon_col:
        df = _valid_coords(df, lat_col, lon_col)
        df = df.rename(columns={lat_col: "latitud", lon_col: "longitud"})
    if "ubigeo" in df.columns:
        df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)
    log_summary(df, "IPRESS Facilities (clean)")
    save_csv(df, PROCESSED / "ipress_clean.csv")
    return df


def clean_emergency_production(df):
    df = standardize_columns(df)
    df = df.drop_duplicates()
    if "ubigeo" in df.columns:
        df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
            if converted.notna().mean() > 0.5:
                df[col] = converted
    log_summary(df, "Emergency Production (clean)")
    save_csv(df, PROCESSED / "emergencia_clean.csv")
    return df


def clean_district_boundaries(gdf):
    gdf = gdf.copy()
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    gdf = gdf.drop_duplicates()
    for cand in ["ubigeo", "ubigeo_dis", "cod_ubigeo", "coddist"]:
        if cand in gdf.columns:
            gdf = gdf.rename(columns={cand: "ubigeo"})
            break
    if "ubigeo" in gdf.columns:
        gdf["ubigeo"] = gdf["ubigeo"].astype(str).str.zfill(6)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    print("  [CRS] District boundaries reprojected to EPSG:4326 (WGS84)")
    log_summary(gdf, "District Boundaries (clean)")
    gdf.to_file(PROCESSED / "distritos_clean.gpkg", driver="GPKG")
    return gdf