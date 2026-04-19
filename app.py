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

    ---
    ## Main Findings

    **Finding 1 — Supply is geographically concentrated.**
    Facility availability is heavily skewed toward Lima-Callao and Arequipa.
    Q1 districts average only 2.96 facilities per 10,000 population versus 5.97 in Q5 —
    roughly a 2× supply gap that compounds with worse access and activity scores.

    **Finding 2 — Spatial isolation is the strongest separator between quintiles.**
    Q1 districts average 9.81 km to the nearest facility versus 1.31 km for Q5,
    a 7.5× spatial gap. Distance dominates the between-quintile variance more than
    either facility count or emergency activity on its own.

    **Finding 3 — The most underserved districts face triple deficits.**
    Districts such as Yaguas, Huacullani, and Kelluyo score in the bottom quintile
    across all three sub-scores simultaneously — low supply, low activity, and high
    distance. At the other extreme, Lima province (EAS 0.82) and Yanahuara (EAS 0.65)
    are the best-served districts in the country.

    **Finding 4 — Rankings are robust overall, but mid-to-high performers shift under re-weighting.**
    Correlating baseline and alternative EAS across all 1,873 districts yields a tight
    diagonal, confirming the overall ranking is stable. However, districts with high
    emergency utilisation relative to their facility count benefit from the alternative
    specification's heavier weight on AS. Yanahuara gains the most (+0.098 delta),
    reflecting disproportionately high emergency activity for its size.
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

    chart_info = [
        (
            "Top & Bottom Districts — Baseline EAS",
            "top_bottom_eas.png",
            "This horizontal bar chart ranks the 15 most and 15 least served districts by baseline EAS. "
            "A bar chart is the natural choice for comparing a single score across many named categories — "
            "a scatter or line plot would obscure the district identities. "
            "The key takeaway is the magnitude of inequality: the best-served district scores more than "
            "10× higher than the worst, and the bottom quintile clusters tightly near zero.",
        ),
        (
            "EAS Distribution — Baseline vs. Alternative",
            "eas_distribution.png",
            "The overlaid histogram with KDE traces shows the full score distribution for both "
            "specifications across all 1,873 districts. Overlaying two distributions in a single "
            "panel makes methodological sensitivity immediately visible without requiring a separate "
            "table. The key takeaway is that both specifications produce right-skewed distributions — "
            "most districts cluster at low EAS values, with a long tail of better-served outliers.",
        ),
        (
            "Baseline vs. Alternative Scatter",
            "baseline_vs_alternative_scatter.png",
            "Each point is one district, plotted against both specifications simultaneously. "
            "A scatter plot is the only chart type that can expose which districts shift rank "
            "under re-weighting and by how much — a bar chart or table cannot show this. "
            "The tight diagonal confirms overall ranking stability; points above the line are "
            "districts that gain under the alternative (higher AS weight), most notably Yanahuara.",
        ),
        (
            "Sub-score Heatmap — Most Underserved Districts",
            "subscore_heatmap.png",
            "The heatmap displays Facility Score, Activity Score, and Access Score side-by-side "
            "for the 30 most underserved districts. A heatmap outperforms grouped bars here because "
            "it lets the eye scan across three dimensions simultaneously for 30 units. "
            "The dominant pattern is near-zero colour across all three columns for most rows, "
            "confirming that the worst-ranked districts face triple deficits, not a single weakness.",
        ),
    ]
    for caption, fname, interpretation in chart_info:
        p = OUTPUT / "figures" / fname
        if p.exists():
            st.image(str(p), caption=caption, use_container_width=True)
        else:
            st.warning(f"Figure not found: {fname}. Run pipeline.py first.")
        st.caption(interpretation)

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
        st.markdown(
            "**Geographic pattern:** Emergency healthcare access is starkly unequal across Peru's "
            "territory. The coastal strip around Lima-Callao and the Arequipa metropolitan area "
            "dominate the green (high-EAS) zones, reflecting the concentration of both IPRESS "
            "facilities and emergency activity in urban centres. The Andean highlands and Amazon "
            "basin appear predominantly red — not simply because facilities are absent, but because "
            "populated centres in those regions face distances to the nearest facility that can "
            "exceed 20 km. This geographic pattern suggests that closing the access gap requires "
            "targeted infrastructure investment in rural and peri-urban areas, not just aggregate "
            "facility expansion."
        )

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
            st.markdown(
                "**Structural inequality:** The quintile table reveals a compounding disadvantage. "
                "Moving from Q5 to Q1, districts do not merely lose on one dimension — facility "
                "count, emergency utilisation, and proximity all deteriorate together. The mean "
                "distance to the nearest facility rises from roughly 1.3 km in Q5 to nearly 10 km "
                "in Q1, while mean facility count nearly halves. This co-movement of all three "
                "sub-scores in the same direction confirms that access inequality in Peru is "
                "structural: the districts least served by supply are also the most spatially "
                "isolated and the least able to generate recorded emergency utilisation."
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
        if "district_name" in metrics.columns:
            compare.insert(1, "district_name", metrics["district_name"])
        compare["delta"] = compare["eas_alternative"] - compare["eas_baseline"]
        st.dataframe(
            compare.sort_values("delta", ascending=False),
            use_container_width=True, height=400,
        )
        st.markdown(
            "**Methodological sensitivity:** The delta column measures how much each district's "
            "score changes when the Activity Score weight rises from 0.333 to 0.40 at the expense "
            "of the Facility Score weight. Large positive deltas identify districts whose emergency "
            "utilisation is high relative to their facility count — they are 'punished' by the "
            "baseline's equal weighting but rewarded once utilisation matters more. "
            "Yanahuara (Arequipa) shows the largest gain (+0.098), reflecting disproportionately "
            "high emergency activity for its facility count. Conversely, districts with large "
            "negative deltas tend to have many facilities but low recorded emergency visits, "
            "suggesting either under-reporting or genuine low demand. The overall tight correlation "
            "between the two scores (visible in the Tab 2 scatter) confirms that the ranking is "
            "robust at the extremes; the alternative specification mainly reshuffles the middle tier."
        )

    except ImportError:
        st.warning("Install streamlit-folium: pip install streamlit-folium")
    except Exception as e:
        st.error(f"Error: {e}. Run pipeline.py first.")