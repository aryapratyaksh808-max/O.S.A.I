
# OSAI System Architecture

## 1. Overview

OSAI follows a modular architecture consisting
of satellite data processing, deep learning,
geospatial intelligence, temporal analysis,
AIS-based vessel attribution, and visualization.

## 2. Processing Pipeline

### Stage 1: Satellite Data

Input:
- Sentinel-1 SAR imagery
- Acquisition metadata
- VV/VH polarization data

Output:
- Validated satellite scenes

### Stage 2: Preprocessing

Operations:
- Image normalization
- Band selection
- Image tiling
- Input preparation

Output:
- Model-ready SAR images

### Stage 3: Segmentation

Operations:
- Deep learning inference
- Pixel-level classification
- Mask generation
- Prediction post-processing

Output:
- Oil spill segmentation mask

### Stage 4: Geospatial Analysis

Operations:
- Mask polygonization
- Coordinate transformation
- Area calculation
- Centroid extraction

Output:
- Spill geometry
- Area in square metres

### Stage 5: Temporal Intelligence

Operations:
- Multi-temporal scene comparison
- Spill observation timeline
- Release-window estimation

Output:
- Probable release-time window

### Stage 6: Environmental Intelligence

Operations:
- Wind data analysis
- Ocean current analysis
- Drift estimation
- Backtracking

Output:
- Probable spill source region

### Stage 7: AIS Attribution

Operations:
- AIS data preprocessing
- Vessel trajectory reconstruction
- Spatial and temporal matching
- Candidate vessel ranking

Output:
- Ranked vessel candidates
- Supporting evidence

### Stage 8: Visualization

Operations:
- Satellite map visualization
- Spill polygon overlay
- Vessel track visualization
- Investigation reporting

Output:
- Investigation dashboard

## 3. Future Infrastructure

The following components are planned:

- Backend REST API
- Database integration
- Incident management
- Automated reporting
- Complete deployment pipeline

Database integration is not part of the
current implementation.
