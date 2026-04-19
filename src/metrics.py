"""
metrics.py — District-level Emergency Access Score (EAS).

Baseline    : EAS = 0.33*FS + 0.33*AS + 0.34*ACS
Alternative : EAS = 0.20*FS + 0.40*AS + 0.40*ACS
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
from src.utils import save_csv, ensure_dirs

PROCESSED     = Path("data/processed")
OUTPUT_TABLES = Path("output/tables")


def _minmax(s):
    s = s.fillna(0)
    rng = s.max() - s.min()
    return pd.Series(np.zeros(len(s)), index=s.index) if rng == 0 else (s - s.min()) / rng


def _norm_ubigeo(df):
    """Cast ubigeo to zero-padded 6-char string, handling float-read columns."""
    if "ubigeo" not in df.columns:
        return df
    df = df.copy()
    df["ubigeo"] = (
        df["ubigeo"].astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .str.zfill(6)
    )
    return df


def build_district_metrics(pop_centers_gdf, ipress_gdf, emergency_df, districts_gdf):
    """Construct district-level metrics and EAS scores."""

    # 1. Facility count per district
    fac_count = _norm_ubigeo(ipress_gdf).groupby("ubigeo").size().reset_index(name="n_facilities")

    # 2. Emergency activity per district
    emg = emergency_df.copy()
    emg.columns = emg.columns.str.lower()
    emg = _norm_ubigeo(emg)
    vol_col = next(
        (c for c in emg.columns if any(k in c for k in ["total", "aten", "consul", "emerg", "prod"])),
        None,
    )
    if vol_col is None:
        raise ValueError(f"Could not detect emergency volume column. Columns: {list(emg.columns)}")
    emg_agg = (
        emg.groupby("ubigeo")[vol_col].sum().reset_index()
           .rename(columns={vol_col: "total_emergency"})
    )

    # 3. Populated-center count and distance per district (exclude unmatched centers)
    pop_agg = (
        _norm_ubigeo(pop_centers_gdf[pop_centers_gdf["ubigeo"].notna()])
        .groupby("ubigeo")
        .agg(n_pop_centers=("ubigeo", "count"),
             mean_dist_km=("dist_nearest_km", "mean"))
        .reset_index()
    )

    # 4. Merge to district table
    dist = _norm_ubigeo(districts_gdf[["ubigeo"]].copy())
    for _name_col in ["district_name", "nombdist", "distrito"]:
        if _name_col in districts_gdf.columns:
            name_map = districts_gdf.drop_duplicates("ubigeo").set_index("ubigeo")[_name_col]
            dist = dist.copy()
            dist["district_name"] = dist["ubigeo"].map(name_map)
            break
    df = (dist.merge(fac_count, on="ubigeo", how="left")
              .merge(emg_agg,   on="ubigeo", how="left")
              .merge(pop_agg,   on="ubigeo", how="left"))
    df["n_facilities"]  = df["n_facilities"].fillna(0)
    df["total_emergency"] = df["total_emergency"].fillna(0)
    df["n_pop_centers"] = df["n_pop_centers"].fillna(0).clip(lower=1)
    df["mean_dist_km"]  = df["mean_dist_km"].fillna(df["mean_dist_km"].median())

    # 5. Per-center rates (n_pop_centers used as denominator — shapefile has no census population)
    df["fac_per_10k"] = df["n_facilities"]    / df["n_pop_centers"] * 10_000
    df["emg_per_10k"] = df["total_emergency"] / df["n_pop_centers"] * 10_000
    df["inv_dist"]    = 1 / (df["mean_dist_km"] + 1)

    # 6. Normalize
    df["fs"]  = _minmax(df["fac_per_10k"])
    df["as_"] = _minmax(df["emg_per_10k"])
    df["acs"] = _minmax(df["inv_dist"])

    # 7. Composite scores
    df["eas_baseline"]    = 0.33*df["fs"] + 0.33*df["as_"] + 0.34*df["acs"]
    df["eas_alternative"] = 0.20*df["fs"] + 0.40*df["as_"] + 0.40*df["acs"]

    # 8. Quintile classification
    for score_col in ["eas_baseline", "eas_alternative"]:
        label = "quintile_" + score_col.split("_")[1]
        df[label] = pd.qcut(
            df[score_col].rank(method="first"), q=5,
            labels=["Q1 (Most Underserved)", "Q2", "Q3", "Q4", "Q5 (Best Served)"],
        )

    ensure_dirs(OUTPUT_TABLES)
    save_csv(df, PROCESSED / "district_metrics.csv")
    save_csv(df, OUTPUT_TABLES / "district_metrics_final.csv")
    print(f"\n[Metrics] District metrics built for {len(df)} districts.")
    return df