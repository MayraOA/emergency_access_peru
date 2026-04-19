"""
data_loader.py — Functions to load raw datasets for the emergency healthcare
access analysis of Peru.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from src.utils import log_summary

RAW = Path("data/raw")


def load_populated_centers(filepath=None) -> gpd.GeoDataFrame:
    """Load the Centros Poblados shapefile (CCPP_IGN100K.shp)."""
    path = filepath or RAW / "CCPP_IGN100K.shp"
    gdf = gpd.read_file(str(path))
    log_summary(gdf, "Populated Centers (raw)")
    return gdf


def load_district_boundaries(filepath=None) -> gpd.GeoDataFrame:
    """Load the DISTRITOS shapefile."""
    path = filepath or RAW / "DISTRITOS.shp"
    gdf = gpd.read_file(str(path))
    log_summary(gdf, "District Boundaries (raw)")
    return gdf


def load_emergency_production(folder=None) -> pd.DataFrame:
    """Load and concatenate all yearly emergency production CSV files.
    
    Files use semicolon as separator.
    """
    folder = Path(folder) if folder else RAW
    files = sorted(folder.glob("emergencia_ipress_*.csv"))
    if not files:
        raise FileNotFoundError(f"No emergency CSV files found in {folder}")
    
    dfs = []
    for f in files:
        year = f.stem.split("_")[-1]
        for encoding in ["latin-1", "cp1252", "utf-8"]:
            try:
                df = pd.read_csv(f, encoding=encoding, sep=";")
                df["year"] = year
                dfs.append(df)
                print(f"  [Loaded] {f.name} — {len(df)} rows")
                break
            except Exception as e:
                print(f"  [Warning] {f.name} with {encoding}: {e}")
                continue

    if not dfs:
        raise ValueError("No emergency files could be loaded.")

    combined = pd.concat(dfs, ignore_index=True)
    log_summary(combined, "Emergency Production (raw, all years)")
    return combined

def load_ipress_facilities(filepath=None) -> pd.DataFrame:
    """Load the MINSA IPRESS health facilities dataset."""
    path = filepath or RAW / "ipress_minsa.csv"
    try:
        df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    log_summary(df, "IPRESS Facilities (raw)")
    return df