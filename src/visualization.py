"""
visualization.py — Static charts and interactive maps.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from pathlib import Path
from src.utils import ensure_dirs

FIGURES = Path("output/figures")
sns.set_theme(style="whitegrid", palette="muted")


def plot_top_bottom_districts(metrics, n=15, save=True):
    """Bar chart: Top-N and Bottom-N districts by baseline EAS.
    
    WHY THIS GRAPH: A horizontal bar chart is the clearest way to compare
    a single numeric score across many named categories. Showing both extremes
    emphasizes the inequality gap.
    """
    ensure_dirs(FIGURES)
    df = metrics.dropna(subset=["eas_baseline"]).sort_values("eas_baseline")
    name_col = "district_name" if "district_name" in df.columns else "ubigeo"
    combined = pd.concat([df.head(n), df.tail(n)])
    colors = ["#e74c3c" if v < df["eas_baseline"].median() else "#2ecc71"
              for v in combined["eas_baseline"]]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(combined[name_col], combined["eas_baseline"], color=colors)
    ax.axvline(df["eas_baseline"].median(), ls="--", color="gray", label="Median")
    ax.set_xlabel("Emergency Access Score (Baseline)")
    ax.set_title(f"Top & Bottom {n} Districts — Baseline EAS")
    ax.legend()
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES / "top_bottom_eas.png", dpi=150)
        print(f"  [Saved] {FIGURES}/top_bottom_eas.png")
    return fig


def plot_score_distribution(metrics, save=True):
    """Histogram + KDE: baseline vs alternative EAS distributions.
    
    WHY THIS GRAPH: Reveals the shape of the access distribution and
    overlaying both specifications shows methodological sensitivity.
    """
    ensure_dirs(FIGURES)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(metrics["eas_baseline"],    kde=True, color="#3498db", label="Baseline",    alpha=0.6, ax=ax)
    sns.histplot(metrics["eas_alternative"], kde=True, color="#e67e22", label="Alternative", alpha=0.6, ax=ax)
    ax.set_xlabel("Emergency Access Score")
    ax.set_ylabel("Number of Districts")
    ax.set_title("Distribution of EAS — Baseline vs. Alternative")
    ax.legend()
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES / "eas_distribution.png", dpi=150)
        print(f"  [Saved] {FIGURES}/eas_distribution.png")
    return fig


def plot_score_scatter(metrics, save=True):
    """Scatter: baseline EAS vs alternative EAS per district.
    
    WHY THIS GRAPH: Districts that diverge from the diagonal are directly
    affected by re-weighting, making methodological differences concrete.
    """
    ensure_dirs(FIGURES)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(metrics["eas_baseline"], metrics["eas_alternative"],
               alpha=0.4, s=15, color="#8e44ad")
    ax.plot([0, 1], [0, 1], ls="--", color="gray", label="y = x")
    ax.set_xlabel("Baseline EAS")
    ax.set_ylabel("Alternative EAS")
    ax.set_title("Baseline vs. Alternative — District Scatter")
    ax.legend()
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES / "baseline_vs_alternative_scatter.png", dpi=150)
        print(f"  [Saved] {FIGURES}/baseline_vs_alternative_scatter.png")
    return fig


def plot_subscore_heatmap(metrics, n=30, save=True):
    """Heatmap of sub-scores for the most underserved districts.
    
    WHY THIS GRAPH: Allows simultaneous comparison of three components
    across many districts, revealing which dimension drives underservice.
    """
    ensure_dirs(FIGURES)
    name_col = "district_name" if "district_name" in metrics.columns else "ubigeo"
    df = (metrics.dropna(subset=["fs", "as_", "acs"])
          .sort_values("eas_baseline").head(n)
          .set_index(name_col)[["fs", "as_", "acs"]])
    df.columns = ["Facility Score", "Activity Score", "Access Score"]
    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(df, cmap="RdYlGn", vmin=0, vmax=1, linewidths=0.3, ax=ax)
    ax.set_title(f"Sub-score Heatmap — {n} Most Underserved Districts")
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES / "subscore_heatmap.png", dpi=150)
        print(f"  [Saved] {FIGURES}/subscore_heatmap.png")
    return fig


def plot_choropleth(districts_gdf, metrics, column="eas_baseline",
                    title="Emergency Access Score", filename="choropleth_eas.png", save=True):
    """Static choropleth map.
    
    WHY THIS MAP: A choropleth on district polygons captures administrative
    boundaries relevant for policy decisions.
    """
    ensure_dirs(FIGURES)
    gdf = districts_gdf.merge(metrics[["ubigeo", column]], on="ubigeo", how="left")
    fig, ax = plt.subplots(figsize=(10, 14))
    gdf.plot(column=column, cmap="RdYlGn", legend=True,
             missing_kwds={"color": "lightgrey", "label": "No data"},
             ax=ax, linewidth=0.1, edgecolor="white")
    ax.set_title(title, fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    if save:
        fig.savefig(FIGURES / filename, dpi=150)
        print(f"  [Saved] {FIGURES}/{filename}")
    return fig


def build_folium_map(districts_gdf, metrics, column="eas_baseline"):
    """Interactive Folium choropleth with tooltips."""
    gdf = districts_gdf.merge(
        metrics[["ubigeo", column, "n_facilities", "total_emergency", "mean_dist_km"]],
        on="ubigeo", how="left"
    ).to_crs("EPSG:4326")

    m = folium.Map(location=[-9.19, -75.015], zoom_start=5, tiles="CartoDB positron")
    folium.Choropleth(
        geo_data=gdf.__geo_interface__,
        data=gdf, columns=["ubigeo", column],
        key_on="feature.properties.ubigeo",
        fill_color="RdYlGn", fill_opacity=0.75, line_opacity=0.2,
        nan_fill_color="lightgrey",
        legend_name=column.replace("_", " ").title(),
    ).add_to(m)
    folium.GeoJson(
        gdf,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["ubigeo", column, "n_facilities", "total_emergency", "mean_dist_km"],
            aliases=["Ubigeo", "EAS Score", "# Facilities", "Emergency Visits", "Avg Dist (km)"],
        ),
        style_function=lambda x: {"fillOpacity": 0},
    ).add_to(m)
    return m