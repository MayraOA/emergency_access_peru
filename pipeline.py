"""
pipeline.py — End-to-end pipeline runner.

Usage:
    python pipeline.py

Place raw files in data/raw/:
  - centros_poblados.csv
  - DISTRITOS.shp (+ .dbf, .prj, .shx)
  - emergencia_ipress.csv
  - ipress_minsa.csv
"""

from src.data_loader import (
    load_populated_centers, load_district_boundaries,
    load_emergency_production, load_ipress_facilities,
)
from src.cleaning import (
    clean_populated_centers, clean_district_boundaries,
    clean_emergency_production, clean_ipress_facilities,
)
from src.geospatial import build_geospatial_layers
from src.metrics import build_district_metrics
from src.visualization import (
    plot_top_bottom_districts, plot_score_distribution,
    plot_score_scatter, plot_subscore_heatmap, plot_choropleth,
)

if __name__ == "__main__":
    print("=" * 60)
    print("  Emergency Healthcare Access Pipeline — Peru")
    print("=" * 60)

    # 1. Load
    pop_raw  = load_populated_centers()
    dist_raw = load_district_boundaries()
    emg_raw  = load_emergency_production()
    ipr_raw  = load_ipress_facilities()

    # 2. Clean
    pop_clean  = clean_populated_centers(pop_raw)
    dist_clean = clean_district_boundaries(dist_raw)
    emg_clean  = clean_emergency_production(emg_raw)
    ipr_clean  = clean_ipress_facilities(ipr_raw)

    # 3. Geospatial
    pop_geo, ipr_geo = build_geospatial_layers(pop_clean, ipr_clean, dist_clean)

    # 4. Metrics
    metrics = build_district_metrics(pop_geo, ipr_geo, emg_clean, dist_clean)

    # 5. Static charts
    plot_top_bottom_districts(metrics)
    plot_score_distribution(metrics)
    plot_score_scatter(metrics)
    plot_subscore_heatmap(metrics)

    # 6. Static maps
    plot_choropleth(dist_clean, metrics, "eas_baseline",
                    "Emergency Access Score — Baseline", "choropleth_eas_baseline.png")
    plot_choropleth(dist_clean, metrics, "eas_alternative",
                    "Emergency Access Score — Alternative", "choropleth_eas_alternative.png")

    print("\n✅ Pipeline complete. Run: streamlit run app.py")