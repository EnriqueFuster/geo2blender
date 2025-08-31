import os
import numpy as np
import rasterio
from PIL import Image
from tqdm import tqdm


def rescale_dsm_global(dsm_path: str):
    """
    Load the full DSM and rescale globally to 16-bit.

    Returns:
        scaled_dsm (np.ndarray): DSM rescaled to 0-65535 (uint16)
        nodata_value (float/int): original DSM nodata value
    """
    with rasterio.open(dsm_path) as src:
        dsm_data = src.read(1).astype(np.float32)
        nodata_value = src.nodata

    # Mask nodata
    valid_mask = dsm_data != nodata_value
    valid_data = np.where(valid_mask, dsm_data, np.nan)

    # Global min/max
    global_min, global_max = np.nanmin(valid_data), np.nanmax(valid_data)
    print(f"Rescaling DSM globally: min={global_min}, max={global_max}")

    # Rescale to 0–65535
    scaled_dsm = ((np.nan_to_num(valid_data, nan=global_min) - global_min)
                  / (global_max - global_min) * 65535).astype(np.uint16)

    return scaled_dsm, nodata_value


def save_dsm_chunk_png(dsm_chunk: np.ndarray, nodata_value, output_path: str):
    """
    Save a DSM chunk as 16-bit PNG without rescaling.
    """
    data_to_save = np.where(dsm_chunk != nodata_value, dsm_chunk, 0)
    img = Image.fromarray(data_to_save.astype(np.uint16), mode="I;16")
    img.save(output_path, format="PNG", optimize=True, compress_level=9)


def save_rgb_chunk_png(rgb_chunk: np.ndarray, nodata_value, output_path: str):
    """
    Save an RGB satellite chunk as PNG without rescaling.
    """
    img_array = np.moveaxis(rgb_chunk, 0, -1).astype(np.uint8)
    img = Image.fromarray(img_array, mode="RGB")
    img.save(output_path, format="PNG", optimize=True, compress_level=9)


def generate_chunks(dsm_path: str, satellite_path: str, output_folder: str, n_rows: int, n_cols: int):
    """
    Split DSM and satellite rasters into grid chunks and save as PNG.

    Args:
        dsm_path: path to merged DSM TIFF
        satellite_path: path to merged satellite TIFF
        output_folder: folder to save PNG chunks
        n_rows: number of rows to split
        n_cols: number of columns to split
    """
    os.makedirs(output_folder, exist_ok=True)

    # Rescale DSM globally once
    scaled_dsm, dsm_nodata = rescale_dsm_global(dsm_path)

    with rasterio.open(dsm_path) as dsm, rasterio.open(satellite_path) as satellite:
        if dsm.crs != satellite.crs:
            raise ValueError("CRS mismatch between DSM and Satellite rasters")

        # Common bounding box
        left = max(dsm.bounds.left, satellite.bounds.left)
        right = min(dsm.bounds.right, satellite.bounds.right)
        bottom = max(dsm.bounds.bottom, satellite.bounds.bottom)
        top = min(dsm.bounds.top, satellite.bounds.top)

        chunk_width = (right - left) / n_cols
        chunk_height = (top - bottom) / n_rows

        for row in tqdm(range(n_rows), desc="Processing rows"):
            for col in range(n_cols):
                chunk_left = left + col * chunk_width
                chunk_right = chunk_left + chunk_width
                chunk_bottom = bottom + row * chunk_height
                chunk_top = chunk_bottom + chunk_height

                # Raster windows
                dsm_window = dsm.window(chunk_left, chunk_bottom, chunk_right, chunk_top)
                satellite_window = satellite.window(chunk_left, chunk_bottom, chunk_right, chunk_top)

                # --- DSM chunk ---
                dsm_chunk = scaled_dsm[
                    int(dsm_window.row_off): int(dsm_window.row_off + dsm_window.height),
                    int(dsm_window.col_off): int(dsm_window.col_off + dsm_window.width)
                ]

                # --- Satellite chunk ---
                satellite_chunk = satellite.read([1, 2, 3], window=satellite_window,
                                                boundless=True, fill_value=satellite.nodata)

                # Output paths
                dsm_chunk_path = os.path.join(output_folder, f"dsm_r{row:03d}_c{col:03d}.png")
                satellite_chunk_path = os.path.join(output_folder, f"satellite_r{row:03d}_c{col:03d}.png")

                # Save PNGs
                save_dsm_chunk_png(dsm_chunk, dsm_nodata, dsm_chunk_path)
                save_rgb_chunk_png(satellite_chunk, satellite.nodata, satellite_chunk_path)

    print(f"🎉 All chunks saved in {output_folder}")
    return output_folder
