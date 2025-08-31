import numpy as np
import rasterio
from rasterio.windows import Window
from PIL import Image
from tqdm import tqdm

Image.MAX_IMAGE_PIXELS = None  # prevent errors with very large images


def export_texture_png(input_tif, output_png, block_size=1024):
    """
    Export a raster (RGB or grayscale) to a PNG texture for Blender.

    Parameters
    ----------
    input_tif : str
        Path to the input GeoTIFF.
    output_png : str
        Path to the output PNG.
    block_size : int
        Number of rows to read per block (to avoid memory issues).
    """
    print(f"🔹 Exporting {input_tif} to texture PNG {output_png}...")

    with rasterio.open(input_tif) as src:
        width, height = src.width, src.height
        bands = src.count

        if bands == 3:
            mode = "RGB"
        elif bands == 4:
            mode = "RGBA"
        else:
            mode = "L"  # grayscale

        img = Image.new(mode, (width, height))

        with tqdm(total=(height // block_size + 1), desc="Writing PNG blocks") as pbar:
            for y_off in range(0, height, block_size):
                h = min(block_size, height - y_off)
                window = Window(0, y_off, width, h)
                block = src.read(window=window)

                if bands in [3, 4]:
                    block = np.transpose(block, (1, 2, 0))  # (bands, h, w) -> (h, w, bands)
                else:
                    block = block[0]  # grayscale

                img_block = Image.fromarray(block.astype(np.uint8), mode=mode)
                img.paste(img_block, (0, y_off))
                pbar.update(1)

        img.save(output_png, format="PNG", optimize=True, compress_level=9)

    print(f"🎉 Texture saved at {output_png}")
    return output_png
