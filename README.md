# LiDAR Terrain Modeling

This repository contains a small, reproducible workflow for terrain-level 3D modeling from airborne/terrestrial LiDAR LAS data. It was built for a 3D modeling and application course assignment, with emphasis on transparent processing steps and report-ready outputs.

## Features

- Direct reading of LAS 1.2 point format 3 data without requiring `laspy`.
- Elevation-quantile denoising for removing obvious high/low outliers.
- Progressive TIN-like ground filtering.
- Cloth-simulation-like ground filtering.
- Ground-point LAS export.
- DEM generation as GeoTIFF plus world file.
- Preview images and algorithm flowcharts for reports.

## Repository Structure

```text
data/        input LAS point cloud
docs/        report text and flowchart assets
outputs/     generated LAS, DEM, preview image, and report-material outputs
src/         processing and drawing scripts
```

Large LAS files are tracked with Git LFS.

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the main workflow:

```powershell
python .\src\terrain_modeling_workflow.py
```

Regenerate flowcharts:

```powershell
python .\src\draw_technical_scheme_flowchart.py
python .\src\draw_progressive_tin_filter_flowchart.py
python .\src\draw_cloth_simulation_filter_flowchart.py
```

Optionally generate a local PPTX summary after the workflow has produced preview images:

```powershell
python .\src\build_report_presentation.py
```

Generated PPTX files are ignored by Git and are not part of the published outputs.

## Workflow

```text
Input LAS point cloud
-> elevation-quantile denoising
-> progressive TIN-like ground filtering
-> cloth-simulation-like ground filtering
-> ground LAS export
-> DEM raster generation
-> preview images and report materials
```

## Data and Outputs

The repository includes the input LAS file used in the experiment and the generated non-PPTX results under `outputs/`, including ground-point LAS files, DEM files, preview images, and report materials.

The filtering code is an educational implementation for course reporting and reproducible learning. It should not be treated as a replacement for production LiDAR processing software.
