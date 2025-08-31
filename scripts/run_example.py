from glob import glob
from geo2blender import config
from geo2blender import config, merge_rasters, export_chunks
import os

# Collect files
dsm_files = glob(os.path.join(config.DSM_DIR, "*.tif"))
satellite_files = glob(os.path.join(config.SATELLITE_DIR, "*.tif"))

# Merge DSM
if dsm_files:
    merged_dsm_path = os.path.join(config.PROCESSING_DIR, config.MERGED_DSM_FILENAME)
    merge_rasters(dsm_files, merged_dsm_path, num_bands=config.DSM_BANDS)

# Merge Satellite
if satellite_files:
    merged_satellite_path = os.path.join(config.PROCESSING_DIR, config.MERGED_SATELLITE_FILENAME)
    merge_rasters(
        satellite_files,
        merged_satellite_path,
        num_bands=config.SATELLITE_BANDS,
        scale_factor=config.SATELLITE_SCALE_FACTOR
    )

# Generate PNG chunks
export_chunks.generate_chunks(
    dsm_path=merged_dsm_path,
    satellite_path=merged_satellite_path,
    output_folder=config.CHUNKS_DIR,
    n_rows=config.CHUNKS_ROWS,
    n_cols=config.CHUNKS_COLS
)