# Geo2Blender — Satellite & DSM preprocessing for Blender

![status](https://img.shields.io/badge/status-alpha-orange)
![python](https://img.shields.io/badge/python-3.13-blue)
![license](https://img.shields.io/badge/license-MIT-green)

**Geo2Blender** is a lightweight Python package/CLI for **merging raster tiles** (e.g. DSM/DTM and satellite orthophotos) and **exporting them as PNGs** that can be directly used in **Blender** as displacement maps and textures.  
It is intended for reproducible workflows without the need to open heavy GIS software.

> ⚠️ This project is in early stage (alpha). The API and CLI may evolve.  
> Tested with datasets from **Spain, England, France, and Switzerland** — note that **data acquisition is not automated** yet and differs by country. See [Input Data](#input-data).

---

## Table of Contents

- [Features](#features)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Using venv + pip](#using-venv--pip)
  - [GDAL/rasterio notes](#gdalgdalrasterio-notes)
- [Input Data](#input-data)
- [Quickstart](#quickstart)
- [CLI Usage](#cli-usage)
- [Python API Usage](#python-api-usage)
- [Technical Notes](#technical-notes)
- [Blender Integration](#blender-integration)
- [Performance & Limitations](#performance--limitations)
- [Known Issues](#known-issues)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Merge raster tiles** (DSM or satellite) into a single GeoTIFF, reprojection handled automatically.
- **Chunked writing** (windowed) to handle large files, with **BigTIFF** output when required.
- **Respects `nodata`**, with configurable resampling and resolution scaling (useful for large satellite imagery).
- **Exports**:
  - **PNG textures** (RGB or grayscale) from merged GeoTIFFs.
  - **Tiled PNGs** (grid of *n_rows × n_cols*) for DSM + satellite, aligned for easy multi‑tile texturing in Blender.

## Repository Structure

```
geo2blender/
  geo2blender/
    cli.py                 # CLI with `merge` and `export` subcommands
    merge_rasters.py       # Core raster merging logic (windowed + reprojection)
    export_merged.py       # Export merged GeoTIFFs to PNG
    export_chunks.py       # Generate aligned DSM + satellite chunk PNGs
    config.py              # Default paths and parameters
  scripts/
    run_example.py         # End-to-end workflow example
  requirements.txt
  LICENSE
  README.md
```

## Requirements

- **Python**: `>=3.13,<3.14`
- **Python packages**:
  - `numpy==2.3.2`
  - `rasterio==1.4.3`
  - `Pillow==11.3.0`
  - `tqdm==4.67.1`
- **System dependencies**: `GDAL/PROJ` libraries and GeoTIFF codecs are required for `rasterio`.

### GDAL/rasterio notes

- Installing rasterio can be tricky on some systems. On Windows, you may need precompiled wheels:  
  👉 [Christoph Gohlke’s geospatial wheels](https://github.com/cgohlke/geospatial-wheels/releases)
- On Linux/macOS, installing from `conda-forge` is usually easier as it bundles GDAL/PROJ.

## Installation

### Using venv + pip

```bash
# 1) Create environment
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Install the package in editable mode (recommended for development)
pip install -e .
```

> ⚠️ Micromamba/conda environments should also work, but have not been fully tested.  

## Input Data

At this stage, **data preparation is manual**. You must download DSM and satellite imagery from the official geoportals of each country and convert them into GeoTIFFs.  

The repository expects the following folder structure (customizable in `geo2blender/config.py`):

```
data/
  sources/
    dsm/         # DSM GeoTIFF tiles (1 band)
    satellite/   # Satellite/orthophoto GeoTIFF tiles (3 bands)
  processing/    # Created automatically; intermediate + final outputs
```

### Geoportal sources

**Satellite imagery**:  
- Switzerland: [swisstopo — SWISSIMAGE 10](https://www.swisstopo.admin.ch/en/orthoimage-swissimage-10)  
- England: [Vertical Aerial Photography Tiles](https://environment.data.gov.uk/survey)  
- France: [IGN BD ORTHO®](https://geoservices.ign.fr/bdortho)  
- Spain: [CNIG Centro de Descargas](https://centrodedescargas.cnig.es/CentroDescargas/buscar-mapa)  

**DSM / Height models**:  
- Switzerland: [swisstopo — swissSURFACE3D Raster](https://www.swisstopo.admin.ch/en/height-model-swisssurface3d-raster#swissSURFACE3D-Raster---Download)  
- England: [Environment Agency — Survey data](https://environment.data.gov.uk/survey)  
- France: [IGN — Correlated DSMs](https://geoservices.ign.fr/modeles-numeriques-de-surfaces-correles)  
- Spain: [CNIG Centro de Descargas](https://centrodedescargas.cnig.es/CentroDescargas/buscar-mapa)  

### Notes

- Each country has **different workflows** for downloading, unzipping, and converting data into GeoTIFFs.  
- Once you have valid `.tif` tiles, place them into the correct folder and proceed with the pipeline.

## Quickstart

1) Place your `.tif` DSM and satellite tiles into `data/sources/dsm` and `data/sources/satellite`.  
2) Run the end-to-end example:

```bash
python scripts/run_example.py
```

This produces:

- `data/processing/dsm_merged.tif`
- `data/processing/satellite_merged.tif`  
- PNG chunks in `data/processing/chunks/`:
  - `dsm_rXXX_cYYY.png` (16‑bit heightmap)
  - `satellite_rXXX_cYYY.png` (8‑bit RGB texture)

## CLI Usage

Two main subcommands are available: **merge** and **export**.

### 1) Merge raster tiles

```bash
python -m geo2blender.cli merge   -i data/sources/dsm/*.tif   -o data/processing/dsm_merged.tif   --bands 1   --scale 1.0
```

### 2) Export merged GeoTIFF to PNG texture

```bash
python -m geo2blender.cli export texture   -i data/processing/satellite_merged.tif   -o data/processing/satellite_texture.png
```

## Python API Usage

```python
from glob import glob
from geo2blender.merge_rasters import merge_rasters
from geo2blender.export_merged import export_texture_png
from geo2blender.export_chunks import generate_chunks

# 1) Merge DSM
dsm_files = glob("data/sources/dsm/*.tif")
merge_rasters(dsm_files, "data/processing/dsm_merged.tif", num_bands=1)

# 2) Merge satellite with scaling
sat_files = glob("data/sources/satellite/*.tif")
merge_rasters(sat_files, "data/processing/satellite_merged.tif", num_bands=3, scale_factor=0.5)

# 3) Export PNG texture
export_texture_png("data/processing/satellite_merged.tif", "data/processing/satellite_texture.png")

# 4) Generate aligned DSM + satellite chunks
generate_chunks(
    dsm_path="data/processing/dsm_merged.tif",
    satellite_path="data/processing/satellite_merged.tif",
    output_folder="data/processing/chunks",
    n_rows=6, n_cols=6
)
```

## Technical Notes

- **Reprojection**: by default to the CRS of the first raster provided.  
- **Windowed writing**: uses `rasterio.windows.Window` for memory efficiency.  
- **BigTIFF**: enabled automatically when file size requires it.  
- **nodata** handling: valid pixels always overwrite `nodata`.  
- **Resampling**: nearest neighbor by default (good for DSM).  
- **Bit depth**:
  - DSM chunks exported as **16‑bit grayscale** (0–65535).  
  - Satellite chunks exported as **8‑bit RGB** (0–255).  

## Blender Integration

1. **DSM heightmaps (16‑bit PNG)**  
   - Import with **Color Space = Non‑Color**.  
   - Use **Displacement modifier** or shader-based displacement.  
   - Adjust **Strength** and **Midlevel** (≈0.5 for normalized DSMs).  

2. **Satellite textures (8‑bit PNG)**  
   - Import with default **sRGB** color space.  
   - Connect to **Base Color** of Principled BSDF.  

3. **Alignment**  
   - DSM and satellite chunks are cut with the same grid and align 1:1.  

## Performance & Limitations

- Reduce satellite resolution with `--scale 0.5` to save memory.  
- Use chunks to avoid loading massive images in Blender.  
- For very large AOIs, consider pre‑clipping data in QGIS/GDAL.  

## Known Issues

- CLI is minimal; `chunks` export is currently Python API only.  
- No automated data download yet.  
- Limited validation for mixed CRS inputs.  

## Roadmap

- CLI support for `chunks`.  
- Configurable resampling methods.  
- Export to EXR 32‑bit heightmaps.  
- Remote COG reading (streaming).  
- Automated geoportal download workflows per country.  

## Contributing

Contributions are welcome!  
Ideas:  
- Add examples and test datasets.  
- Improve CLI and configuration.  
- Implement automated download scripts for supported countries.  

```bash
# Suggested testing setup
pytest -q
ruff check .
```

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE).

---

**Author**: Enrique Fuster Palop
