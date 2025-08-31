import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.warp import reproject
from rasterio.transform import from_bounds
from glob import glob
from tqdm import tqdm
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Disable DecompressionBombError

def reproject_rasters_to_crs(src_datasets, target_crs):
    """Reproject all rasters to a common CRS."""
    reprojected = []
    for src in src_datasets:
        if src.crs != target_crs:
            memfile = rasterio.io.MemoryFile()
            with memfile.open(
                driver="GTiff",
                height=src.height,
                width=src.width,
                count=src.count,
                dtype=src.dtypes[0],
                crs=target_crs,
                transform=src.transform,
            ) as tmp:
                for band in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, band),
                        destination=rasterio.band(tmp, band),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=src.transform,   
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear,
                    )
            reprojected.append(memfile.open())
        else:
            reprojected.append(src)
    return reprojected


def compute_merge_metadata(src_datasets, scale_factor=1.0):
    """Compute bounds, resolution, transform and metadata for raster merging."""
    bounds = [src.bounds for src in src_datasets]
    minx = min(b.left for b in bounds)
    miny = min(b.bottom for b in bounds)
    maxx = max(b.right for b in bounds)
    maxy = max(b.top for b in bounds)

    ref = src_datasets[0]
    target_res = ref.res[0] / scale_factor
    target_crs = ref.crs
    dtype = ref.dtypes[0]

    width = int(np.ceil((maxx - minx) / target_res))
    height = int(np.ceil((maxy - miny) / target_res))
    transform = from_bounds(minx, miny, maxx, maxy, width, height)

    return {
        "transform": transform,
        "crs": target_crs,
        "dtype": dtype,
        "res": target_res,
        "width": width,
        "height": height,
        "bounds": (minx, miny, maxx, maxy),
    }


def write_raster_blocks(src_datasets, output_path, metadata, num_bands,
                        block_size=1024, resampling=Resampling.bilinear):
    """Blockwise raster merging routine for N-band rasters."""
    nodata_value = src_datasets[0].nodata
    if nodata_value is None:
        nodata_value = -9999 if num_bands == 1 else 0

    output_meta = {
        "driver": "GTiff",
        "height": metadata["height"],
        "width": metadata["width"],
        "count": num_bands,
        "crs": metadata["crs"],
        "transform": metadata["transform"],
        "dtype": metadata["dtype"],
        "nodata": nodata_value,
        "compress": "lzw",
    }

    total_blocks = ((metadata["height"] + block_size - 1) // block_size) * (
        (metadata["width"] + block_size - 1) // block_size
    )
    block_counter = 0

    with rasterio.open(output_path, "w", BIGTIFF="YES", **output_meta) as dst:
        for y_off in range(0, metadata["height"], block_size):
            for x_off in range(0, metadata["width"], block_size):
                h = min(block_size, metadata["height"] - y_off)
                w = min(block_size, metadata["width"] - x_off)
                window = Window(x_off, y_off, w, h)

                block_data = np.full((num_bands, h, w), nodata_value, dtype=metadata["dtype"])

                for src in src_datasets:
                    for band in range(1, num_bands + 1):
                        temp = np.full((h, w), nodata_value, dtype=metadata["dtype"])
                        reproject(
                            source=rasterio.band(src, band),
                            destination=temp,
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=metadata["transform"] * metadata["transform"].translation(x_off, y_off),
                            dst_crs=metadata["crs"],
                            resampling=resampling,
                            src_nodata=src.nodata,
                            dst_nodata=nodata_value,
                        )
                        mask = temp != nodata_value
                        block_data[band - 1, mask] = temp[mask]

                dst.write(block_data, window=window)

                block_counter += 1
                print(f"Progress: {block_counter}/{total_blocks} blocks merged", end="\r")

    print(f"\n✅ Merge completed: {output_path}")
    return output_path


def merge_rasters(file_list, output_path, num_bands, scale_factor=1.0, **kwargs):
    """High-level function to merge multiple rasters into one."""
    print(f"🔹 Merging {len(file_list)} rasters with {num_bands} bands (scale_factor={scale_factor})...")

    src_paths = [rasterio.open(f) for f in file_list]
    src_datasets = reproject_rasters_to_crs(src_paths, target_crs=src_paths[0].crs)

    metadata = compute_merge_metadata(src_datasets, scale_factor=scale_factor)
    result = write_raster_blocks(src_datasets, output_path, metadata, num_bands, **kwargs)

    for s in src_datasets:
        s.close()
    return result

