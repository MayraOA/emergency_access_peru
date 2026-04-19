"""
data_loader.py — Functions to load raw datasets for the emergency healthcare
access analysis of Peru.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from src.utils import log_summary

RAW = Path("data/raw")


def load_populated_centers(filepath=None) -> pd.DataFrame:
    """Load the Centros Poblados dataset."""
    path = filepath or RAW / "centros_poblados.csv"
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    log_summary(df, "Populated Centers (raw)")
    return df


def load_district_boundaries(filepath=None) -> gpd.GeoDataFrame:
    """Load the DISTRITOS shapefile."""
    path = filepath or RAW / "DISTRITOS.shp"
    gdf = gpd.read_file(str(path))
    log_summary(gdf, "District Boundaries (raw)")
    return gdf


def load_emergency_production(filepath=None) -> pd.DataFrame:
    """Load the emergency care production by IPRESS dataset."""
    path = filepath or RAW / "emergencia_ipress.csv"
    try:
        df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    log_summary(df, "Emergency Production (raw)")
    return df


def load_ipress_facilities(filepath=None) -> pd.DataFrame:
    """Load the MINSA IPRESS health facilities dataset."""
    path = filepath or RAW / "ipress_minsa.csv"
    try:
        df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    log_summary(df, "IPRESS Facilities (raw)")
    return df