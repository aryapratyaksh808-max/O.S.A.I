
# OSAI --- Oil Spill Attribution Intelligence

> **An AI-assisted satellite intelligence system for detecting marine
> oil spills, measuring their extent, estimating a probable release
> window, and identifying vessels that may be associated with the
> incident using historical AIS data.**

OSAI is designed as an investigation-support prototype. It combines
Synthetic Aperture Radar (SAR) imagery, geospatial analysis,
ocean/environmental context, and vessel-tracking data to produce an
explainable incident report for human review.

**Important:** OSAI does not prove that a particular vessel caused a
spill. It ranks potentially relevant vessels using spatial and temporal
evidence. Final attribution requires verification by competent
authorities and additional evidence.

------------------------------------------------------------------------

## Contents

-   [1. Problem Statement](#1-problem-statement)
-   [2. Project Objectives](#2-project-objectives)
-   [3. High-Level Architecture](#3-high-level-architecture)
-   [4. Complete End-to-End Workflow](#4-complete-end-to-end-workflow)
-   [5. Module Breakdown](#5-module-breakdown)
-   [6. Oil-Spill Segmentation](#6-oil-spill-segmentation)
-   [7. Geospatial Area Calculation](#7-geospatial-area-calculation)
-   [8. Release-Time and Source
    Estimation](#8-release-time-and-source-estimation)
-   [9. AIS-Based Vessel Attribution](#9-ais-based-vessel-attribution)
-   [10. Backend and API Architecture](#10-backend-and-api-architecture)
-   [11. Database Design](#11-database-design)
-   [12. Dashboard and Investigation
    Output](#12-dashboard-and-investigation-output)
-   [13. Technology Stack](#13-technology-stack)
-   [14. Suggested Repository
    Structure](#14-suggested-repository-structure)
-   [15. Running the Project](#15-running-the-project)
-   [16. Model Evaluation](#16-model-evaluation)
-   [17. Limitations and Responsible
    Use](#17-limitations-and-responsible-use)
-   [18. Future Improvements](#18-future-improvements)

------------------------------------------------------------------------

## 1. Problem Statement

Oil spills can cause serious damage to marine ecosystems, coastal
communities, and the maritime economy. Detecting a spill is only the
first step: an investigation also needs to understand its size, when it
may have occurred, how it may have moved, and which vessels were
operating in the relevant area.

OSAI addresses this workflow by connecting satellite-based spill
segmentation with geospatial measurements, environmental drift context,
and historical Automatic Identification System (AIS) vessel data.

## 2. Project Objectives

1.  Detect and segment suspected oil-spill regions in Sentinel-1 SAR
    imagery.
2.  Convert segmented pixels into georeferenced spill polygons.
3.  Estimate spill area and geometric properties in real-world units.
4.  Use available multi-temporal observations to estimate a probable
    release-time window.
5.  Use wind/current information, when available, to support backward
    source-region estimation.
6.  Search historical AIS tracks around the estimated time and region.
7.  Rank candidate vessels using transparent spatial and temporal
    evidence.
8.  Present the incident, evidence, confidence, and candidate vessels
    through an investigation dashboard and report.

## 3. High-Level Architecture

``` mermaid
flowchart TD
    A["Sentinel-1 SAR imagery"] --> B["Data ingestion and validation"]
    B --> C["SAR preprocessing"]
    C --> D["Oil-spill segmentation model"]
    D --> E["Binary/class segmentation mask"]
    E --> F["Geospatial post-processing"]
    F --> G["Spill polygon and measurements"]

    G --> H["Multi-temporal analysis"]
    H --> I["Probable release-time window"]
    G --> J["Environmental drift analysis"]
    I --> K["Source-region estimation"]
    J --> K

    L["Historical AIS data"] --> M["AIS cleaning and track reconstruction"]
    K --> N["Spatiotemporal candidate search"]
    M --> N
    N --> O["Vessel evidence scoring and ranking"]

    G --> P["Incident database"]
    I --> P
    K --> P
    O --> P

    P --> Q["Backend REST API"]
    Q --> R["Investigation dashboard"]
    Q --> S["HTML/PDF incident report"]
```

### Architectural layers

  -----------------------------------------------------------------------
  Layer                               Responsibility
  ----------------------------------- -----------------------------------
  Data layer                          Satellite scenes, AIS records, and
                                      environmental datasets

  Processing layer                    SAR preprocessing, segmentation,
                                      and geospatial analysis

  Intelligence layer                  Release-window estimation, drift
                                      analysis, and vessel ranking

  Backend layer                       API orchestration, validation,
                                      persistence, and job status

  Presentation layer                  Map-based dashboard, evidence view,
                                      and reports
  -----------------------------------------------------------------------

The system should keep detection, measurement, and attribution as
separate stages. This makes results easier to test and prevents a
segmentation result from being treated as proof of vessel
responsibility.

## 4. Complete End-to-End Workflow

### Step 1 --- Satellite data ingestion

-   Acquire a Sentinel-1 SAR scene covering the area of interest.
-   Read scene metadata such as acquisition time, orbit information,
    polarization, and geospatial reference.
-   Validate that the scene covers the requested region and is suitable
    for processing.
-   Where available, collect earlier/later scenes covering the same
    region for temporal comparison.

**Output:** validated SAR scene(s) with acquisition metadata.

### Step 2 --- SAR preprocessing

Prepare the SAR data for the segmentation model. Depending on the source
product and model requirements, preprocessing may include:

1.  Reading the required VV/VH polarization bands.
2.  Applying the appropriate calibration and noise-handling steps.
3.  Applying terrain/geometric correction when required by the chosen
    product workflow.
4.  Converting or normalizing values using the same method used during
    model training.
5.  Cropping the region of interest and dividing large scenes into
    model-sized tiles.
6.  Retaining the geospatial transform and CRS for every tile.

Training and inference preprocessing must be consistent. A model trained
on one scaling or polarization convention may perform poorly if
inference uses another.

**Output:** normalized, georeferenced SAR tiles.

### Step 3 --- Oil-spill segmentation

-   Send each tile to the trained segmentation model.
-   Generate a pixel-wise prediction mask.
-   Combine tile predictions back into the scene while handling tile
    boundaries.
-   Apply a documented threshold or class-selection rule.
-   Remove or flag tiny/noisy regions only through validated
    post-processing rules.

**Output:** predicted oil-spill mask and model confidence/probability
map, if the model provides one.

### Step 4 --- Geospatial post-processing

-   Convert connected spill regions in the mask into georeferenced
    polygons.
-   Preserve the source scene's coordinate reference system.
-   Repair invalid geometries where appropriate.
-   Remove duplicate or overlapping tile-edge polygons.
-   Calculate polygon centroid, perimeter, length, width, and
    orientation where useful.

**Output:** one or more georeferenced spill polygons.

### Step 5 --- Spill area measurement

Calculate area from the georeferenced polygon using an appropriate
projected CRS or geodesic area calculation. Do not assume that every
pixel has the same ground area unless the image geometry and processing
justify that assumption.

**Output:** spill area in square metres and hectares, with the
measurement method and CRS recorded.

### Step 6 --- Temporal analysis and release-window estimation

If multiple observations are available:

-   Compare spill masks and polygon areas across acquisition times.
-   Track changes in area, shape, centroid, and position.
-   Build an observed area-versus-time series, `A(t)`.
-   Use the observations and a documented growth/drift assumption to
    estimate a **probable release-time window**.

A single satellite image generally cannot establish the exact release
time. The system should return a time interval and
confidence/uncertainty, not an unsupported exact timestamp.

**Output:** estimated release window with supporting observations.

### Step 7 --- Environmental drift and source-region estimation

When suitable wind and ocean-current data are available:

-   Retrieve environmental conditions for the relevant time period.
-   Use a drift/backtracking method to estimate where the observed slick
    may have originated.
-   Account for uncertainty in environmental data, slick behaviour, and
    observation timing.
-   Produce a probable source region or search corridor rather than
    claiming an exact release coordinate.

**Output:** source-region estimate, uncertainty region, and
environmental inputs used.

### Step 8 --- AIS data preparation

Load historical AIS records for a sufficiently broad time and geographic
window. Useful fields include:

-   MMSI and, where available, IMO number
-   Latitude and longitude
-   Timestamp
-   Speed over ground (SOG)
-   Course over ground (COG)
-   Heading, when available
-   Vessel identity/type metadata, when available

Clean invalid coordinates and timestamps, handle duplicate records,
normalize time zones, and reconstruct vessel tracks in chronological
order.

**Output:** cleaned vessel trajectories.

### Step 9 --- Spatiotemporal vessel candidate search

Compare AIS trajectories against the estimated source region and
release-time window.

For each vessel, evaluate evidence such as:

1.  **Temporal compatibility:** was the vessel present during the
    probable release window?
2.  **Spatial compatibility:** did its track pass through or near the
    probable source region?
3.  **Trajectory compatibility:** is its movement consistent with the
    investigation's spatial assumptions?
4.  **Data quality:** how complete and reliable are the vessel's AIS
    observations?
5.  **Environmental compatibility:** where supported, does the vessel's
    location fit the drift/backtracking analysis?

Do not treat AIS proximity alone as proof of a spill. AIS gaps,
spoofing, transmission intervals, and uncertainty in drift modelling can
affect the result.

**Output:** candidate vessels with individual evidence features.

### Step 10 --- Explainable attribution ranking

Calculate a documented candidate score from the available evidence. Keep
the component scores visible rather than returning only a black-box
ranking.

An illustrative scoring structure is:

``` text
candidate_score =
    temporal_compatibility_weight * temporal_score
  + spatial_compatibility_weight * spatial_score
  + trajectory_compatibility_weight * trajectory_score
  + data_quality_weight * data_quality_score
```

The weights and score ranges must be calibrated and validated before
operational use. Missing evidence should be represented explicitly; it
should not silently receive a favourable score.

**Output:** ranked candidate list, evidence breakdown, and
confidence/uncertainty notes.

### Step 11 --- Persistence, dashboard, and report

Store the incident, source-scene metadata, model output references,
spill geometry, measurements, release-window estimate, environmental
inputs, AIS evidence, and candidate ranking.

The dashboard retrieves these results through backend APIs and presents
them as an investigation case. A report can summarize the same evidence
for review and export.

------------------------------------------------------------------------

## 5. Module Breakdown

  ---------------------------------------------------------------------------
  Module            Input             Main operation       Output
  ----------------- ----------------- -------------------- ------------------
  Satellite         Sentinel-1 scene  Download/read and    Scene and metadata
  ingestion                           validate metadata    

  SAR preprocessing SAR bands         Normalize, crop,     Model-ready tiles
                                      tile, preserve       
                                      georeferencing       

  Segmentation      SAR tiles         Pixel-wise model     Spill mask
                                      inference            

  Geospatial        Mask + scene      Polygonize and clean Spill polygons
  processing        transform         geometries           

  Area measurement  Spill polygons    Projected/geodesic   m² and hectares
                                      area calculation     

  Temporal analysis Multiple dated    Compare area and     Probable release
                    observations      position over time   window

  Drift analysis    Spill             Backtrack probable   Source region and
                    observations +    source region        uncertainty
                    wind/current                           

  AIS processing    Historical AIS    Clean and            Vessel
                    records           reconstruct tracks   trajectories

  Attribution       Source/time       Feature extraction   Ranked vessels
                    estimate + tracks and candidate        
                                      scoring              

  Reporting         Incident evidence Assemble maps,       Dashboard/report
                                      metrics, and         
                                      explanations         
  ---------------------------------------------------------------------------

## 6. Oil-Spill Segmentation

Segmentation is the computer-vision stage that classifies pixels in a
SAR image rather than assigning one label to the entire image.

### Model pipeline

``` mermaid
flowchart LR
    A["SAR tile (VV/VH)"] --> B["Preprocessing"]
    B --> C["Segmentation model"]
    C --> D["Pixel probability map"]
    D --> E["Threshold / class selection"]
    E --> F["Binary spill mask"]
    F --> G["Polygonization"]
```

### Training and inference

**Training** - Prepare labelled SAR tiles and corresponding masks. -
Split data into training, validation, and test sets at scene/geographic
level where possible to reduce spatial leakage. - Apply the same
preprocessing intended for inference. - Train the segmentation model and
monitor validation metrics. - Save the best checkpoint and the exact
configuration used.

**Inference** - Load the trained checkpoint. - Apply the identical
input-band order, normalization, tile size, and model configuration. -
Predict each tile and reconstruct the full-scene mask. - Save the mask
with enough metadata to reproduce the result.

### Evaluation metrics

-   **IoU (Intersection over Union):** overlap between predicted and
    ground-truth regions.
-   **Dice/F1:** overlap metric that balances precision and recall.
-   **Precision:** fraction of predicted spill pixels that are correct.
-   **Recall:** fraction of actual spill pixels detected.
-   **mIoU:** mean IoU across evaluated classes.

Overall pixel accuracy alone can be misleading because sea/background
pixels may dominate the image. Report oil-class precision, recall, IoU,
and Dice separately.

## 7. Geospatial Area Calculation

The segmentation mask is in pixel coordinates; investigation
measurements must be in real-world coordinates.

Recommended process:

1.  Read the raster geotransform and CRS.
2.  Convert each spill region to a polygon using the raster's geospatial
    transform.
3.  Reproject the polygon to a suitable local projected CRS before
    planar area measurement, or use a geodesic area method.
4.  Calculate area in square metres and convert to hectares:

``` text
area_hectares = area_square_metres / 10,000
```

5.  Record the CRS, method, source scene, and any geometry
    simplification.

**Important:** Sentinel-1 is a radar imaging system. Pixel ground
dimensions depend on the product, acquisition geometry, processing, and
location. Do not calculate area from satellite altitude or slant-range
distance alone. Use the product's georeferencing and appropriate
ground-area calculation.

## 8. Release-Time and Source Estimation

OSAI separates two related questions:

-   **When might the spill have been released?** --- temporal
    estimation.
-   **Where might it have originated?** --- spatial backtracking.

A sequence of dated observations can constrain the release window.
Environmental drift modelling can then help estimate a probable source
region. Both results should carry uncertainty because satellite revisit
gaps, weather/current data resolution, and oil behaviour limit
precision.

Suggested stored fields:

``` text
first_observed_at
last_observed_at
estimated_release_start
estimated_release_end
source_region_geometry
environmental_data_sources
estimation_method
uncertainty_notes
```

These are conceptual field names; adapt them to the actual database
schema.

## 9. AIS-Based Vessel Attribution

AIS is used to reconstruct vessel movement, not to directly identify an
oil discharge.

### Candidate matching

For each vessel track:

1.  Select AIS points within the relevant time window.
2.  Check whether the track intersects or approaches the estimated
    source region.
3.  Calculate distance and time differences using geospatial methods.
4.  Summarize track continuity and data quality.
5.  Calculate transparent evidence features.
6.  Rank candidates and retain the supporting AIS points/track segment.

### Example evidence table

  -----------------------------------------------------------------------
  Evidence                            What it indicates
  ----------------------------------- -----------------------------------
  Time match                          Vessel was in the area during the
                                      estimated release window

  Distance match                      Vessel passed near the estimated
                                      source region

  Track continuity                    AIS observations are sufficient to
                                      assess movement

  Course/speed context                Helps interpret the vessel's
                                      movement

  Drift compatibility                 Track is spatially plausible under
                                      the environmental model
  -----------------------------------------------------------------------

The result should be worded as **"potentially associated candidate"**,
not "confirmed polluter".

## 10. Backend and API Architecture

The backend coordinates processing jobs and exposes results to the
dashboard. The segmentation and geospatial workloads can run as Python
services, while a separate application backend can manage users,
incidents, persistence, and API orchestration.

A service-oriented deployment can follow this pattern:

``` mermaid
flowchart TD
    UI["React dashboard"] --> API["Application backend / REST API"]
    API --> DB[("Relational + geospatial database")]
    API --> JOB["Processing job coordinator"]
    JOB --> PY["Python intelligence service"]
    PY --> SEG["SAR segmentation"]
    PY --> GEO["Geospatial analysis"]
    PY --> AIS["AIS matching and ranking"]
    PY --> ENV["Environmental drift analysis"]
    PY --> DB
    API --> REPORT["Report generation"]
    REPORT --> UI
```

### Suggested API contract

The following routes are a suggested interface, not a claim that every
route is already implemented:

  ----------------------------------------------------------------------------------
  Method                  Endpoint                           Purpose
  ----------------------- ---------------------------------- -----------------------
  `POST`                  `/api/incidents`                   Create an investigation

  `POST`                  `/api/incidents/{id}/scenes`       Register/upload a
                                                             satellite scene

  `POST`                  `/api/incidents/{id}/process`      Start the processing
                                                             pipeline

  `GET`                   `/api/incidents/{id}`              Get incident summary
                                                             and status

  `GET`                   `/api/incidents/{id}/spill`        Get spill geometry and
                                                             measurements

  `GET`                   `/api/incidents/{id}/timeline`     Get temporal
                                                             observations and
                                                             release window

  `GET`                   `/api/incidents/{id}/candidates`   Get ranked vessel
                                                             candidates and evidence

  `GET`                   `/api/incidents/{id}/report`       Generate or retrieve
                                                             the report
  ----------------------------------------------------------------------------------

Long-running satellite/model jobs should run asynchronously. The API
should return a job/incident identifier and expose processing status
rather than keeping an HTTP request open throughout inference.

## 11. Database Design

A relational database with geospatial support is suitable for storing
investigation records and geometries.

Suggested logical entities:

  -----------------------------------------------------------------------
  Entity                              Important data
  ----------------------------------- -----------------------------------
  `Incident`                          ID, status, region, created time

  `SatelliteScene`                    Product ID, acquisition time,
                                      orbit, polarization, file
                                      reference, CRS

  `SegmentationResult`                Model version, mask reference,
                                      thresholds, evaluation/config
                                      metadata

  `SpillObservation`                  Observation time, polygon, area,
                                      perimeter, centroid

  `ReleaseEstimate`                   Estimated time interval, source
                                      region, method, uncertainty

  `EnvironmentalObservation`          Time, location, wind/current
                                      values, source

  `AISRecord`                         MMSI/IMO, timestamp, position, SOG,
                                      COG, heading

  `VesselCandidate`                   Incident, vessel identity, total
                                      score, evidence breakdown

  `ProcessingJob`                     Job type, status, start/end time,
                                      error details
  -----------------------------------------------------------------------

Use spatial column types and spatial indexes for spill polygons, source
regions, and vessel positions where supported. Store large raster files
and model artifacts in file/object storage; keep their paths and
metadata in the database.

## 12. Dashboard and Investigation Output

The dashboard should present the investigation as a sequence of
evidence-backed stages.

Recommended views:

-   **Incident overview:** status, area of interest, acquisition time,
    and processing state.
-   **Satellite view:** original SAR scene, predicted mask, and spill
    polygon overlay.
-   **Measurements:** area in m²/hectares, perimeter, centroid, and
    geometry.
-   **Timeline:** satellite observations and probable release-time
    window.
-   **Source analysis:** estimated source region and environmental
    assumptions.
-   **AIS map:** vessel tracks, source region, and relevant time window.
-   **Candidate table:** ranked vessels with transparent evidence and
    data-quality indicators.
-   **Report:** downloadable incident summary with maps, methodology,
    and limitations.

Every result should be traceable to its input scene, model version,
processing configuration, and data source.

## 13. Technology Stack

The following is the intended/reference stack for the architecture. Keep
only the technologies actually used in the implementation when updating
this table.

  -----------------------------------------------------------------------
  Area                                Technology / library
  ----------------------------------- -----------------------------------
  Satellite input                     Sentinel-1 SAR

  Model development                   Python, PyTorch

  Image processing                    OpenCV, NumPy

  Tabular processing                  Pandas

  Geospatial processing               Rasterio, GeoPandas, Shapely, GDAL

  Environmental data                  Suitable wind and ocean-current
                                      datasets/APIs

  Vessel tracking                     Historical AIS data

  Application backend                 Spring Boot or Python FastAPI,
                                      according to the deployed backend

  ML/geospatial service               Python REST service

  Database                            MySQL for relational records;
                                      PostgreSQL/PostGIS if spatial
                                      database features are adopted

  Frontend                            React.js

  Map visualization                   Leaflet or another geospatial map
                                      library

  Reporting                           HTML/PDF report generation
  -----------------------------------------------------------------------

**Architecture note:** Spring Boot + MySQL and Python REST services have
been considered for the application integration. FastAPI +
PostgreSQL/PostGIS + React is another suitable reference architecture.
Do not run both backend alternatives by default; document the one
present in the actual repository.

## 14. Suggested Repository Structure

``` text
OSAI/
├── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── maps/
│   └── package.json
│
├── backend/
│   ├── src/
│   ├── controllers/
│   ├── services/
│   ├── models/
│   └── application configuration
│
├── intelligence-service/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── segmentation/
│   │   ├── models/
│   │   ├── inference/
│   │   └── training/
│   ├── geospatial/
│   ├── temporal_analysis/
│   ├── drift_analysis/
│   ├── ais/
│   ├── attribution/
│   ├── reporting/
│   └── requirements.txt
│
├── data/
│   ├── samples/
│   └── README.md
│
├── models/
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   └── methodology.md
│
└── .env.example
```

This is a suggested organization. Match it to the actual folders and
filenames in the repository rather than creating empty folders just to
match the diagram.

## 15. Running the Project

Exact commands depend on the repository's current implementation. A
typical local setup is:

### Prerequisites

-   Python version compatible with the ML dependencies
-   PyTorch build compatible with the selected CPU/CUDA environment
-   Node.js and npm for the frontend
-   Java/JDK and Maven or Gradle if Spring Boot is used
-   Database configured for the selected backend
-   Access to Sentinel-1 scenes, AIS data, and optional environmental
    data

### Configuration

Create local environment configuration from the example file and provide
the required paths, database connection, and data-provider credentials.

``` env
# Example placeholders — use the variable names required by your code
DATABASE_URL=
SATELLITE_DATA_DIR=
AIS_DATA_SOURCE=
ENVIRONMENT_DATA_SOURCE=
MODEL_CHECKPOINT=
```

Never commit API keys, passwords, private AIS datasets, or other
secrets.

### Typical development sequence

1.  Install the Python intelligence-service dependencies.
2.  Configure and start the database.
3.  Start the application backend.
4.  Start the Python processing service.
5.  Install frontend dependencies and start the dashboard.
6.  Create an incident and submit a supported Sentinel-1 scene.
7.  Run the pipeline and inspect the generated evidence.

Replace this section with tested, exact commands once the actual scripts
and package files are finalized.

## 16. Model Evaluation

Evaluate segmentation and attribution separately.

### Segmentation evaluation

Report at least:

-   Oil-class IoU
-   Oil-class Dice/F1
-   Oil-class precision and recall
-   Confusion matrix
-   Performance across different scenes/regions and conditions

Keep a held-out test set separate from training and model selection.
Avoid splitting adjacent tiles from the same scene across training and
test if that would cause spatial leakage.

### Attribution evaluation

Where verified incident labels are available, evaluate:

-   Whether the known vessel appears in the top-k candidates
-   Precision/recall at the chosen candidate threshold
-   Ranking quality (for example, MRR or NDCG)
-   Sensitivity to missing AIS observations and environmental
    uncertainty

Do not report an attribution accuracy unless there is a defensible
labelled evaluation dataset.

## 17. Limitations and Responsible Use

-   SAR dark spots are not always oil. Look-alikes can include low-wind
    areas, biogenic films, rain cells, and other phenomena.
-   Segmentation quality depends on training data, labels, sensor
    conditions, and preprocessing.
-   Area estimates depend on georeferencing, geometry quality, and the
    chosen measurement method.
-   A single image usually cannot establish the exact spill release
    time.
-   Drift estimates are uncertain and depend on environmental data
    quality and model assumptions.
-   AIS data can be incomplete, delayed, inaccurate, unavailable, or
    manipulated.
-   A vessel near a spill is not automatically responsible for it.
-   Candidate ranking is an investigative lead, not a legal conclusion.

OSAI should therefore expose its evidence, assumptions, data gaps, and
uncertainty to the analyst. Any enforcement decision must be based on
independent verification and applicable procedures.

## 18. Future Improvements

-   Multi-temporal Sentinel-1 analysis and automated scene discovery.
-   Stronger look-alike discrimination and uncertainty-aware
    segmentation.
-   Better calibrated area and uncertainty estimates.
-   Validated ocean-drift/backtracking models.
-   AIS gap detection and robust trajectory reconstruction.
-   Explainable, calibrated vessel candidate ranking.
-   PostGIS-backed spatial queries and scalable asynchronous processing.
-   Reproducible experiment tracking and model versioning.
-   Automated evidence bundles and audit logs.

------------------------------------------------------------------------

## Project Status

OSAI is an investigation-support prototype. The architecture above
describes the complete intended workflow; individual modules should be
marked as **Implemented**, **In Progress**, or **Planned** based on the
current repository and tested behaviour.

**Do not interpret a reference repository, pretrained checkpoint, or
reported benchmark as an OSAI result unless it has been integrated and
independently tested on OSAI's own data.**
