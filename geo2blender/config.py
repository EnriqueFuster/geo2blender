import os

# Base data path: relative or absolute
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
PROJECT_DIR = "examples/project_template"

BASE_DATA_PATH = os.path.join(REPO_ROOT, PROJECT_DIR)

# Input/output directories
SOURCES_SUBDIR = "sources"
PROCESSING_SUBDIR = "processing"
SOURCES_DIR = os.path.join(BASE_DATA_PATH, SOURCES_SUBDIR)
PROCESSING_DIR = os.path.join(BASE_DATA_PATH, PROCESSING_SUBDIR)
os.makedirs(PROCESSING_DIR, exist_ok=True)

# Subfolders for different raster types
DSM_SUBDIR = "dsm"
SATELLITE_SUBDIR = "satellite"
DSM_DIR = os.path.join(SOURCES_DIR, DSM_SUBDIR)
SATELLITE_DIR = os.path.join(SOURCES_DIR, SATELLITE_SUBDIR)

# Output filenames
MERGED_DSM_FILENAME = "dsm_merged.tif"
MERGED_SATELLITE_FILENAME = "satellite_merged.tif"

# Merge settings
DSM_BANDS = 1
SATELLITE_BANDS = 3
SATELLITE_SCALE_FACTOR = 0.5

# Export PNG chunks settings
CHUNKS_SUBDIR = "chunks"
CHUNKS_DIR = os.path.join(PROCESSING_DIR, CHUNKS_SUBDIR)
os.makedirs(CHUNKS_DIR, exist_ok=True) 
CHUNKS_ROWS = 4
CHUNKS_COLS = 4 