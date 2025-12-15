### High Priority Implementation Plan (Actionable Tasks)

#### Overview
Goal: Deliver four high‑priority improvements with clear data pipelines, code changes, tests, and outputs. The plan fits the current repo structure (`main.py`, `src/risk.py`, `src/quadtree.py`) and adds new modules without breaking existing flows.

---

### 1) Historical Disaster Data Validation
Purpose: Validate computed `risk_score` against historical earthquake impacts to quantify accuracy and calibrate thresholds.

- Scope & Objectives
  - Collect 5–10 years of historical events (epicenter, magnitude, depth, intensity/MMI, date/time, impact proxies if available).
  - Define matching rules between model output and historical events for validation.
  - Produce accuracy metrics and a calibration report.

- Data Sources (choose ≥1)
  - BNPB/InaRISK public datasets (events and impact summaries, if accessible).
  - USGS ComCat (for completeness and a baseline) — CSV/GeoJSON export.
  - BMKG historical catalogs (if available for bulk download).

- Data Model & Storage
  - New folder: `data/historical/`
  - Files:
    - `historical_events.csv` with columns: `event_id,date,time,latitude,longitude,magnitude,depth,intensity,region_name[,impact_fatalities,impact_economic]`
    - `validation_matches.csv` (output): `event_id, matched_regions, max_risk_score, predicted_risk_level, observed_intensity, match_radius_km, time_window_days`

- Matching & Validation Logic
  - Spatial: match regions/points within `R km` of the event epicenter (start with 50 km; sensitivity study at 25/75/100 km).
  - Temporal: for time‑windowed features, use event date; if not time‑varying, the current model is static; note limitation.
  - Scoring comparison: compare `risk_level` vs observed `intensity` or damage proxy using a mapping table.
  - Metrics: confusion matrix (risk_level vs observed class), accuracy, macro F1, calibration curve, Brier score (if probabilistic), top‑N hit rate for regional ranking.

- Code Tasks
  - Add `src/validation.py`:
    - `load_historical_events(filepath)`
    - `match_events_to_regions(events_df, regions_df, radius_km=50)`
    - `evaluate_against_model(events_df, regional_stats_df)` returns metrics dict + `validation_matches` dataframe
    - `generate_validation_report(metrics, output_dir)` writes `output/reports/validation_report.md`
  - Update `main.py` (optional CLI flags):
    - `--validate-historical` to run the validation pipeline after risk computation.
    - Save `validation_matches.csv` and the report.

- Tests
  - Add `tests` in `test_implementation.py` or `test_validation.py`:
    - Fixture synthetic events near high‑risk and low‑risk regions → expect higher match scores near high‑risk.
    - Unit tests for distance matching and metrics aggregation.

- Deliverables
  - `output/reports/validation_report.md` with metrics, confusion matrix, and calibration notes.
  - `output/data/validation_matches.csv` with matches per event.

- Acceptance Criteria
  - Reproducible pipeline with documented parameters (radius/time window).
  - Baseline accuracy metrics produced without manual steps.

---

### 2) BMKG Data Integration (Near Real‑Time Ingestion)
Purpose: Ingest BMKG earthquake feeds to refresh the dataset and enable timely risk assessments.

- Scope & Objectives
  - Fetch latest earthquake events from BMKG feed/API (or official RSS/JSON if API is restricted).
  - Normalize to project schema and persist to `data/` with timestamps.

- Architecture
  - Pull model (cron or manual run) → normalize → append to `data/earthquake_data.csv` (or a new `data/earthquake_live.csv`).
  - Configurable via `.env` or `config/bmkg.json` (endpoints, rate limits, time window).

- Data Flow
  - Source: BMKG official feed (e.g., `autogempa` XML/RSS) or JSON endpoint if available.
  - Transform: map fields to `latitude,longitude,magnitude,depth,intensity,frequency,plate_zone,region_name`.
    - If `intensity`/`frequency` missing, derive defaults; log missingness.
  - Load: write `data/earthquake_live.csv` with an `ingested_at` column.

- Code Tasks
  - New module `src/integrations/bmkg.py`:
    - `fetch_latest_events(since=None)` → list of dicts
    - `normalize_events(raw)` → DataFrame with project columns
    - `save_live_events(df, path='data/earthquake_live.csv')`
  - Update `main.py`:
    - CLI flag `--use-live` to read from `earthquake_live.csv` if present.
    - Merge live + historical CSVs with de‑duplication on `(date, lat, lon, magnitude)`.
  - Add simple retry/backoff and network error handling; log to `output/logs/bmkg_ingest.log`.

- Tests
  - Mock BMKG responses (XML/JSON samples) and test normalization.
  - Test de‑duplication and schema conformity.

- Deliverables
  - `src/integrations/bmkg.py` with unit tests.
  - `data/earthquake_live.csv` created after a successful run.
  - Ingestion log file.

- Acceptance Criteria
  - One‑command ingestion with clear logs and idempotent runs.

- Risks/Mitigations
  - API changes/unavailability → keep a fallback parser for alternative official feeds; feature‑flag usage.

---

### 3) Population Density Data Enhancement
Purpose: Incorporate population exposure into `risk_score` (the model already supports `population_density` weight but lacks data ingestion).

- Scope & Approach
  - Start with administrative‑level density (province/city) mapped to `region_name` in the dataset.
  - Optionally progress to gridded datasets (WorldPop, GHSL) and compute zonal stats per region.

- Data Sources
  - BPS (Badan Pusat Statistik) tables for population and area → density per admin unit.
  - WorldPop (1km gridded), GHSL — optional for finer granularity.

- Data Model
  - New file: `data/population_density.csv` with columns: `region_name,population,population_density,source,year`.

- ETL & Integration
  - New `src/features/population.py`:
    - `load_population_density(filepath)`
    - `join_density(earthquake_df, density_df, on='region_name')` → adds `population_density`
  - Update `main.py` flow:
    - After loading earthquake data, left‑join density by `region_name`.
    - Pass `population_density` to `RiskCalculator.calculate_risk_score` or ensure present for `calculate_enhanced_risk_score` (it already supports an optional density in the non‑enhanced path; extend enhanced path if needed).

- Validation & QA
  - Unit test joins for coverage (all/most regions receive density, log missing).
  - Sensitivity: compare average `risk_score` shifts before/after density inclusion.

- Deliverables
  - `data/population_density.csv` (document source + year).
  - Updated figures showing impact of density on provincial comparisons.

- Acceptance Criteria
  - Pipeline runs with no missing critical joins (>95% region coverage), and the density weight contributes to scoring.

---

### 4) Infrastructure Critical Facilities Mapping
Purpose: Map critical facilities and produce exposure/proximity features to support risk interpretation and future response planning.

- Scope & Facilities
  - Hospitals, schools (shelters), bridges, primary roads. Start with hospitals + primary roads for MVP.

- Data Sources
  - OpenStreetMap via Overpass API (key: `amenity=hospital`, `highway=primary|trunk`, `bridge=yes`).
  - Local government open data portals if available; BPBD datasets when accessible.

- Features to Compute
  - Nearest facility distance per region/point (km).
  - Facility density within buffers (e.g., count of hospitals within 10 km).

- Data Model
  - `data/infrastructure/` folder:
    - `hospitals.geojson` (or CSV with `name,latitude,longitude`)
    - `roads.geojson`/`roads.csv`
  - Output features saved to `output/data/infrastructure_features.csv` per `region_name`.

- Code Tasks
  - New `src/features/infrastructure.py`:
    - `fetch_osm_pois(bbox_or_regions, feature_filters)` (optional; or pre‑download and store)
    - `build_balltree(df)` for facilities
    - `compute_nearest_distance(points_df, poi_tree)`
    - `compute_density(points_df, pois_df, radius_km)`
  - Update `main.py` (optional flag `--build-infra-features`):
    - Load POIs, compute features for region centroids or all points.
    - Save `output/data/infrastructure_features.csv` and optionally merge into visualizations.

- Visualization
  - Enhance `visualize_regional_analysis` to overlay top hospital locations and annotate nearest distances for high‑risk regions.

- Tests
  - Unit tests with small synthetic POIs ensuring nearest distance/density calculations are correct.

- Acceptance Criteria
  - Reproducible feature computation with saved CSV; distances reasonable upon spot‑checks.

---

### Cross‑Cutting Concerns
- Configuration & Secrets
  - Add `config/` folder and `.env.example`; document endpoints and tokens (none required for OSM Overpass, but rate limits apply).
- Logging
  - Write ingestion/validation logs to `output/logs/` with timestamped filenames.
- Reproducibility & Versioning
  - Record data source versions and fetch dates inside CSV metadata or companion README.
- CI/Test Coverage
  - Extend `test_implementation.py` or add new test files for new modules; aim for unit coverage on transformations.

### Milestones & Timeline (suggested)
- Week 1: Population density ETL + integration; unit tests; updated visuals.
- Week 2: Infrastructure features (hospitals + roads) + overlays; tests.
- Week 3: BMKG ingestion module + merge pipeline; mocks & tests.
- Week 4: Historical validation pipeline + report; baseline metrics; calibration notes.

### Success Criteria (per item)
- Historical validation: Report with metrics generated in one run; clear baseline accuracy.
- BMKG integration: `earthquake_live.csv` created and deduplicated; logs clean.
- Population density: `population_density.csv` joined to ≥95% regions; scores reflect density weight.
- Infrastructure mapping: `infrastructure_features.csv` produced; nearest distance/density computed and visualized.

### Immediate Next Steps (ordered)
1. Create folders: `data/historical/`, `data/infrastructure/`, `src/integrations/`, `src/features/`, `output/logs/`, `output/reports/`.
2. Draft `data/population_density.csv` (BPS) and wire join in `main.py`.
3. Prototype `src/integrations/bmkg.py` with mocked feed and save flow.
4. Implement `src/validation.py` skeleton and a tiny synthetic validation test.
5. Plan OSM extraction bbox (Pulau Jawa) and cache POIs under `data/infrastructure/`.