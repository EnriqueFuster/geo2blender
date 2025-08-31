import argparse
from geo2blender.merge_rasters import merge_rasters
from geo2blender.export import export_texture_png

def main():
    parser = argparse.ArgumentParser(
        description="Geo2Blender CLI - preprocess raster data for Blender"
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- Merge command ---
    merge_parser = subparsers.add_parser("merge", help="Merge multiple raster tiles")
    merge_parser.add_argument(
        "-i", "--input", nargs="+", required=True, help="Input raster files (GeoTIFF)"
    )
    merge_parser.add_argument(
        "-o", "--output", required=True, help="Output merged raster path"
    )
    merge_parser.add_argument(
        "-b", "--bands", type=int, default=1, help="Number of bands in the output raster"
    )
    merge_parser.add_argument(
        "-s", "--scale", type=float, default=1.0, help="Optional scale factor (downsampling)"
    )

    # --- Export command ---
    export_parser = subparsers.add_parser("export", help="Export raster to PNG for Blender")
    export_parser.add_argument(
        "-i", "--input", required=True, help="Input raster file (GeoTIFF)"
    )
    export_parser.add_argument(
        "-o", "--output", required=True, help="Output PNG file"
    )
    # Por ahora solo export_texture_png, más adelante puedes añadir heightmap
    export_parser.add_argument(
        "-m", "--mode", choices=["texture"], default="texture",
        help="Export mode (currently only 'texture')"
    )

    args = parser.parse_args()

    if args.command == "merge":
        merge_rasters(args.input, args.output, num_bands=args.bands, scale_factor=args.scale)
    elif args.command == "export":
        if args.mode == "texture":
            export_texture_png(args.input, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
