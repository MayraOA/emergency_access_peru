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


def clean_populated_centers(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clean the Centros Poblados shapefile."""
    gdf = gdf.copy()
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    gdf = gdf.drop_duplicates()

    # Reproject to WGS84
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Extract lat/lon from geometry
    gdf["longitud"] = gdf.geometry.x
    gdf["latitud"]  = gdf.geometry.y

    # Normalize ubigeo if present
    ubigeo_candidates = ["ubigeo", "cod_ubigeo", "codigou"]
    for cand in ubigeo_candidates:
        if cand in gdf.columns:
            gdf = gdf.rename(columns={cand: "ubigeo"})
            break
    if "ubigeo" in gdf.columns:
        gdf["ubigeo"] = gdf["ubigeo"].astype(str).str.zfill(6)

    # Normalize population column
    pop_candidates = ["poblacion", "pob_censo", "población", "pob"]
    for cand in pop_candidates:
        if cand in gdf.columns:
            gdf = gdf.rename(columns={cand: "poblacion"})
            break
    if "poblacion" in gdf.columns:
        gdf["poblacion"] = pd.to_numeric(gdf["poblacion"], errors="coerce").fillna(0).astype(int)
    else:
        gdf["poblacion"] = 0

    log_summary(gdf, "Populated Centers (clean)")
    ensure_dirs(PROCESSED)
    # Save as GeoPackage and also as CSV for later use
    gdf.to_file(PROCESSED / "centros_poblados_clean.gpkg", driver="GPKG")
    save_csv(
        gdf.drop(columns="geometry"),
        PROCESSED / "centros_poblados_clean.csv"
    )
    return gdf


def clean_ipress_facilities(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the IPRESS health facilities dataset.
    
    Coordinates are in UTM (NORTE/ESTE, EPSG:32718).
    We convert them to WGS84 lat/lon.
    """
    df = standardize_columns(df)
    df = df.drop_duplicates()

    if "ubigeo" in df.columns:
        df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)

    # Convert UTM coordinates (norte/este) to lat/lon
    if "norte" in df.columns and "este" in df.columns:
        df["norte"] = pd.to_numeric(df["norte"], errors="coerce")
        df["este"]  = pd.to_numeric(df["este"],  errors="coerce")
        df = df.dropna(subset=["norte", "este"]).copy()

        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:32718", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df["este"].values, df["norte"].values)
        df["longitud"] = lon
        df["latitud"]  = lat

        # Filter to Peru bounding box
        mask = (
            df["latitud"].between(LAT_MIN, LAT_MAX)
            & df["longitud"].between(LON_MIN, LON_MAX)
        )
        print(f"  [Coords] Dropped {(~mask).sum()} IPRESS rows with invalid coordinates.")
        df = df[mask].reset_index(drop=True)

    log_summary(df, "IPRESS Facilities (clean)")
    save_csv(df, PROCESSED / "ipress_clean.csv")
    return df


def clean_emergency_production(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the emergency care production dataset (all years combined)."""
    
    # Some files have all columns merged into one due to mixed separators.
    # Detect and fix those columns.
    bad_cols = [c for c in df.columns if "," in c or ";" in c]
    if bad_cols:
        # Keep only properly parsed columns
        good_cols = [c for c in df.columns if "," not in c and ";" not in c]
        df = df[good_cols].copy()

    df = standardize_columns(df)
    df = df.drop_duplicates()

    if "ubigeo" in df.columns:
        df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)

    for col in df.columns:
        if col == "year":
            continue
        if df[col].dtypes == object:
            converted = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""), errors="coerce"
            )
            if converted.notna().mean() > 0.5:
                df[col] = converted

    log_summary(df, "Emergency Production (clean)")
    save_csv(df, PROCESSED / "emergencia_clean.csv")
    return df


def clean_district_boundaries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Standardize the district boundaries GeoDataFrame."""
    gdf = gdf.copy()
    gdf.columns = [c.strip().lower() for c in gdf.columns]
    gdf = gdf.drop_duplicates()

    # DISTRITOS.shp uses 'iddist' as district code — build ubigeo from it
    if "ubigeo" not in gdf.columns:
        if "iddist" in gdf.columns:
            gdf["ubigeo"] = gdf["iddist"].astype(str).str.zfill(6)
        elif "codccpp" in gdf.columns:
            gdf["ubigeo"] = gdf["codccpp"].astype(str).str.zfill(6)
    else:
        gdf["ubigeo"] = gdf["ubigeo"].astype(str).str.zfill(6)

    # Keep district name
    if "distrito" in gdf.columns:
        gdf["district_name"] = gdf["distrito"]

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    print("  [CRS] District boundaries reprojected to EPSG:4326 (WGS84)")
    log_summary(gdf, "District Boundaries (clean)")
    gdf.to_file(PROCESSED / "distritos_clean.gpkg", driver="GPKG")
    return gdf