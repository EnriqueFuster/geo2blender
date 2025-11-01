import os
from glob import glob
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from geo2blender import config
from geo2blender.merge_rasters import merge_rasters
from geo2blender.export_chunks import generate_chunks


def main():
    # Collect files
    dsm_files = glob(os.path.join(config.DSM_DIR, "*.tif"))
    satellite_files = glob(os.path.join(config.SATELLITE_DIR, "*.tif"))

    merged_dsm_path = os.path.join(config.PROCESSING_DIR, config.MERGED_DSM_FILENAME)
    merged_satellite_path = os.path.join(config.PROCESSING_DIR, config.MERGED_SATELLITE_FILENAME)

    # Merge DSM
    if dsm_files:
        merged_dsm_path = os.path.join(config.PROCESSING_DIR, config.MERGED_DSM_FILENAME)
        print(f"🛰️ Merging DSM files into {merged_dsm_path} ...")
        merge_rasters(dsm_files, merged_dsm_path, num_bands=config.DSM_BANDS)
    else:
        print("⚠️ No DSM files found, skipping DSM merge.")

    # # Merge Satellite
    if satellite_files:
        merged_satellite_path = os.path.join(config.PROCESSING_DIR, config.MERGED_SATELLITE_FILENAME)
        print(f"🛰️ Merging Satellite files into {merged_satellite_path} ...")
        merge_rasters(
            satellite_files,
            merged_satellite_path,
            num_bands=config.SATELLITE_BANDS,
            scale_factor=config.SATELLITE_SCALE_FACTOR
        )
    else:
        print("⚠️ No Satellite files found, skipping Satellite merge.")

    # Generate PNG chunks
    if merged_dsm_path and merged_satellite_path:
        print(f"🗂️ Generating PNG chunks into {config.CHUNKS_DIR} ...")
        generate_chunks(
            dsm_path=merged_dsm_path,
            satellite_path=merged_satellite_path,
            output_folder=config.CHUNKS_DIR,
            n_rows=config.CHUNKS_ROWS,
            n_cols=config.CHUNKS_COLS
        )
    else:
        print("⚠️ Skipping chunk generation: missing DSM or Satellite merged files.")


if __name__ == "__main__":
    main()
