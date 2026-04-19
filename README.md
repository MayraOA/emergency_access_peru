# Emergency Healthcare Access Inequality in Peru

## What does this project do?
Builds a district-level geospatial analytics pipeline to measure and compare
emergency healthcare access across Peru's ~1,874 districts.

## Main Analytical Goal
Identify which districts are most underserved in emergency healthcare access
and what evidence supports that conclusion.

## Datasets Used
| Dataset | Source |
|---------|--------|
| Populated Centers | datosabiertos.gob.pe |
| District Boundaries | DISTRITOS.shp — d2cml-ai GitHub |
| Emergency Production by IPRESS | datos.susalud.gob.pe |
| IPRESS Health Facilities | datosabiertos.gob.pe — MINSA |

## Data Cleaning
- Column names standardized (lowercase + underscores).
- Duplicates removed; invalid coordinates filtered.
- Ubigeo codes zero-padded to 6 digits.
- Geometries reprojected to EPSG:4326; distances in EPSG:32718.

## District-level Metrics — Emergency Access Score (EAS)
| Component | Measure |
|-----------|---------|
| Facility Score (FS) | Facilities per 10,000 population |
| Activity Score (AS) | Emergency visits per 10,000 population |
| Access Score (ACS) | 1 / (mean distance km + 1) |

**Baseline**: EAS = 0.33 FS + 0.33 AS + 0.34 ACS
**Alternative**: EAS = 0.20 FS + 0.40 AS + 0.40 ACS

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline
Place raw data files in `data/raw/`, then:
```bash
python pipeline.py
```

## Running the Streamlit App
```bash
streamlit run app.py
```

## Main Findings
*(To be completed after running the pipeline with real data)*

## Limitations
- Euclidean distances — not road-network.
- Population data may be outdated.
- Emergency production data may have coverage gaps.