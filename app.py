"""
app.py — Streamlit application for Emergency Healthcare Access in Peru.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
from pathlib import Path

st.set_page_config(
    page_title="Emergency Healthcare Access — Peru",
    page_icon="🏥",
    layout="wide",
)

PROCESSED = Path("data/processed")
OUTPUT    = Path("output")


@st.cache_data
def load_metrics():
    return pd.read_csv(PROCESSED / "district_metrics.csv", dtype={"ubigeo": str})

@st.cache_data
def load_districts():
    return gpd.read_file(PROCESSED / "distritos_clean.gpkg")

@st.cache_data
def load_pop_centers():
    return pd.read_csv(PROCESSED / "pop_centers_geo.csv", dtype={"ubigeo": str})


tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data & Methodology",
    "📊 Static Analysis",
    "🗺️ GeoSpatial Results",
    "🔍 Interactive Exploration",
])


# ── TAB 1 ────────────────────────────────────────────────────────────────────
with tab1:
    st.title("Emergency Healthcare Access Inequality in Peru")
    st.markdown("""
    ## Problem Statement
    Access to emergency healthcare is unequally distributed across Peru's ~1,873 districts.
    This project builds a **district-level Emergency Access Score (EAS)** to identify
    which districts are most underserved.

    ---
    ## Data Sources
    | Dataset | Source | Key Variables |
    |---------|--------|---------------|
    | Populated Centers | datosabiertos.gob.pe | lat, lon, population |
    | District Boundaries | DISTRITOS.shp (GitHub) | ubigeo, geometry |
    | Emergency Production | datos.susalud.gob.pe | ubigeo, emergency visits |
    | IPRESS Facilities | datosabiertos.gob.pe — MINSA | ubigeo, lat, lon |

    ---
    ## Cleaning Summary
    - Column names standardized to lowercase + underscores.
    - Duplicate rows removed.
    - Coordinates outside Peru's bounding box removed.
    - Ubigeo codes zero-padded to 6 digits.
    - Boundaries reprojected to **EPSG:4326**; distances computed in **EPSG:32718**.

    ---
    ## Methodology — Emergency Access Score (EAS)
    | Component | Measure | Rationale |
    |-----------|---------|-----------|
    | Facility Score (FS) | Facilities per 10,000 population | Supply availability |
    | Activity Score (AS) | Emergency visits per 10,000 population | Actual utilization |
    | Access Score (ACS) | 1 / (mean distance km + 1) | Proximity of settlements |

    **Baseline**: EAS = 0.333 FS + 0.333 AS + 0.334 ACS *(weights sum to 1; 0.334 on ACS absorbs rounding)*
    **Alternative**: EAS = 0.20 FS + 0.40 AS + 0.40 ACS

    ---
    ## Limitations
    - Distances are Euclidean, not road-network.
    - Population data may be outdated.
    - Emergency production data may have coverage gaps.
    """)


# ── TAB 2 ────────────────────────────────────────────────────────────────────
with tab2:
    st.title("Static Analysis")
    metrics = load_metrics()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Districts",     f"{len(metrics):,}")
    c2.metric("Mean EAS (Baseline)", f"{metrics['eas_baseline'].mean():.3f}")
    c3.metric("Std Dev EAS",         f"{metrics['eas_baseline'].std():.3f}")
    st.markdown("---")

    for caption, fname in [
        ("Top & Bottom Districts — Baseline EAS",          "top_bottom_eas.png"),
        ("EAS Distribution — Baseline vs. Alternative",    "eas_distribution.png"),
        ("Baseline vs. Alternative Scatter",               "baseline_vs_alternative_scatter.png"),
        ("Sub-score Heatmap — Most Underserved Districts", "subscore_heatmap.png"),
    ]:
        p = OUTPUT / "figures" / fname
        if p.exists():
            st.image(str(p), caption=caption, use_container_width=True)
        else:
            st.warning(f"Figure not found: {fname}. Run pipeline.py first.")

    st.markdown("---")
    st.subheader("District Metrics Table")
    st.dataframe(
        metrics.sort_values("eas_baseline", ascending=False).reset_index(drop=True),
        use_container_width=True, height=400,
    )


# ── TAB 3 ────────────────────────────────────────────────────────────────────
with tab3:
    st.title("GeoSpatial Results")
    try:
        districts = load_districts()
        metrics   = load_metrics()

        spec    = st.radio("Specification:", ["Baseline EAS", "Alternative EAS"], horizontal=True)
        col_map = "eas_baseline" if spec == "Baseline EAS" else "eas_alternative"

        p = OUTPUT / f"figures/choropleth_{col_map}.png"
        if p.exists():
            st.image(str(p), caption=f"Choropleth — {spec}", use_container_width=True)
        else:
            st.warning("Static choropleth not found. Run pipeline.py first.")

        st.markdown("---")
        q_col = "quintile_baseline" if "baseline" in col_map else "quintile_alternative"
        if q_col in metrics.columns:
            st.subheader("Quintile Summary")
            st.dataframe(
                metrics.groupby(q_col)
                       .agg(n_districts=("ubigeo", "count"),
                            mean_eas=(col_map, "mean"),
                            mean_facilities=("n_facilities", "mean"),
                            mean_dist=("mean_dist_km", "mean"))
                       .reset_index(),
                use_container_width=True,
            )
    except Exception as e:
        st.error(f"Could not load data: {e}. Run pipeline.py first.")


# ── TAB 4 ────────────────────────────────────────────────────────────────────
with tab4:
    st.title("Interactive Exploration")
    try:
        from streamlit_folium import st_folium
        from src.visualization import build_folium_map

        districts = load_districts()
        metrics   = load_metrics()

        spec = st.selectbox("Specification:", ["eas_baseline", "eas_alternative"])
        m    = build_folium_map(districts, metrics, column=spec)
        st_folium(m, width=900, height=600)

        st.markdown("---")
        st.subheader("Baseline vs. Alternative Comparison")
        compare = metrics[["ubigeo", "eas_baseline", "eas_alternative"]].copy()
        compare["delta"] = compare["eas_alternative"] - compare["eas_baseline"]
        st.dataframe(
            compare.sort_values("delta", ascending=False),
            use_container_width=True, height=400,
        )

    except ImportError:
        st.warning("Install streamlit-folium: pip install streamlit-folium")
    except Exception as e:
        st.error(f"Error: {e}. Run pipeline.py first.")