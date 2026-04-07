# 3D Modeling and Application: LiDAR Terrain Modeling

This repository contains a reproducible course assignment workflow for terrain-level 3D modeling from a LAS point cloud.

The original LAS files and generated large data products are not included in the open-source package because they are large and may be course-provided data. Place your LAS file in `data/` before running the workflow.

## What is included

- `src/terrain_lidar_assignment.py`: LAS reader, denoising, progressive TIN-like ground filtering, cloth-simulation-like ground filtering, ground LAS export, DEM generation, and preview images.
- `src/make_report_pptx.py`: a minimal PPTX report generator using generated preview images.
- `src/draw_*.py`: scripts for drawing report flowcharts.
- `docs/report_sections.md`: report text that can be copied into the internship report.
- `docs/assets/`: algorithm and technical-scheme flowcharts.

## What is not included

- Raw LAS point cloud data, such as `20251126150027848.las`.
- Generated large files, such as `ground_tin.las`, `ground_csf.las`, and DEM rasters.
- Course PPTX templates or assignment files.

## Quick Start

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Put the input point cloud here:

```text
data/20251126150027848.las
```

3. Run the terrain modeling workflow:

```powershell
python .\src\terrain_lidar_assignment.py
```

4. Optional: regenerate the flowcharts:

```powershell
python .\src\draw_4_1_flowchart.py
python .\src\draw_progressive_tin_flowchart.py
python .\src\draw_cloth_filter_flowchart.py
```

5. Optional: generate the brief PPTX report after the workflow outputs are produced:

```powershell
python .\src\make_report_pptx.py
```

## Main Workflow

```text
Input LAS point cloud
-> elevation quantile denoising
-> progressive TIN-like ground filtering
-> cloth-simulation-like ground filtering
-> ground LAS export
-> DEM raster generation
-> preview images and report materials
```

## Notes

The implementation avoids requiring `laspy`, `rasterio`, or `python-pptx`; it parses LAS 1.2 point format 3 directly and writes minimal GeoTIFF/PPTX outputs with standard Python libraries plus `numpy`, `scipy`, `Pillow`, and `matplotlib`.

The filtering implementation is an educational approximation of progressive TIN filtering and cloth simulation filtering. It is intended for course reporting and reproducible learning, not as a replacement for production-grade LiDAR processing software.
