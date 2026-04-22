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
| GeoPandas methodology reference | d2cml-ai GitHub — spatial join and CRS handling patterns |

## Data Download Instructions

### 1. Populated Centers shapefile
- **URL:** https://www.datosabiertos.gob.pe/dataset/dataset-centros-poblados
- **Save to:** `data/raw/`
- **Files to download (keep original filenames):**
  `CCPP_IGN100K.cpg`, `CCPP_IGN100K.dbf`, `CCPP_IGN100K.prj`, `CCPP_IGN100K.sbn`,
  `CCPP_IGN100K.sbx`, `CCPP_IGN100K.shp`, `CCPP_IGN100K.shp.xml`, `CCPP_IGN100K.shx`
- **Note:** All eight sidecar files must be present in the same directory for the shapefile to load correctly.

### 2. District Boundaries shapefile
- **URL:** https://github.com/d2cml-ai/Data-Science-Python/tree/main/_data/Folium
- **Save to:** `data/raw/`
- **Files to download (keep original filenames):**
  `DISTRITOS.shp`, `DISTRITOS.dbf`, `DISTRITOS.prj`, `DISTRITOS.shx`
- **Note:** Download each file individually via the "Raw" button on GitHub, or clone the repository and copy the four files from `_data/Folium/`.

### 3. Emergency Production CSVs
- **URL:** http://datos.susalud.gob.pe/dataset/consulta-c1-produccion-asistencial-en-emergencia-por-ipress
- **Save to:** `data/raw/`
- **Filename convention:** Rename each yearly file to `emergencia_ipress_YYYY.csv`
  (e.g. `emergencia_ipress_2024.csv`). The pipeline will auto-detect all files matching
  `emergencia_ipress_*.csv`.
- **Note:** Files use semicolon (`;`) as the column separator and latin-1 encoding. Do not open and re-save in Excel, as this may corrupt the encoding.

### 4. IPRESS Health Facilities
- **URL:** https://www.datosabiertos.gob.pe/dataset/minsa-ipress
- **Save to:** `data/raw/ipress_minsa.csv`
- **Note:** The coordinate columns are labelled `NORTE` and `ESTE` but contain decimal-degree values (WGS84), not UTM. The pipeline handles the remapping automatically.

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
1. **Supply is geographically concentrated.** Q1 districts average 2.96 facilities per 10,000
   population versus 5.97 in Q5 — roughly a 2× supply gap that compounds with worse access and
   activity scores. Facility availability is heavily skewed toward Lima-Callao and Arequipa.

2. **Spatial isolation is the strongest separator between quintiles.** Q1 districts average
   9.81 km to the nearest facility versus 1.31 km for Q5, a 7.5× spatial gap. Distance
   dominates the between-quintile variance more than facility count or emergency activity alone.

3. **The most underserved districts face triple deficits.** Yaguas, Huacullani, Kelluyo, and
   similar districts score in the bottom quintile on all three sub-scores simultaneously.
   At the other extreme, Lima province (EAS 0.82) and Yanahuara (EAS 0.65) are the best served.

4. **Rankings are robust overall, but mid-to-high performers shift under re-weighting.**
   The baseline and alternative EAS correlate tightly across all 1,873 districts. Yanahuara
   gains the most under the alternative specification (+0.098 delta) due to disproportionately
   high emergency activity relative to its facility count.

## Limitations
- Euclidean distances — not road-network.
- Population data may be outdated.
- Emergency production data may have coverage gaps.