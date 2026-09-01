import os
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset source path: configurable via environment variable, falling back to default archive location
DEFAULT_RAW_DATASET_PATH = Path(r"C:\Users\sward\Downloads\archive\RecipeNLG_dataset.csv")
RAW_DATASET_PATH = Path(os.getenv("RECIPENLG_DATASET_PATH", str(DEFAULT_RAW_DATASET_PATH)))

# Output directories
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# Output artifacts
PARQUET_PATH = PROCESSED_DATA_DIR / "recipes.parquet"
SQLITE_INDEX_PATH = PROCESSED_DATA_DIR / "ingredient_index.sqlite"
STATS_PATH = PROCESSED_DATA_DIR / "processing_stats.json"
MALFORMED_LOG_PATH = LOGS_DIR / "malformed_rows.log"

# Processing configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "50000"))
PROGRESS_LOG_INTERVAL = int(os.getenv("PROGRESS_LOG_INTERVAL", "100000"))
