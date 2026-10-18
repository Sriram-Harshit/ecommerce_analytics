import pandas as pd
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "default"

# In-memory singleton cache to avoid re-reading multi-megabyte CSVs on every request
_DATASET_CACHE: Dict[str, pd.DataFrame] = {}

DATASET_FILES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}


def get_dataset(name: str) -> pd.DataFrame:
    """
    Lazily loads and caches a single dataset by name.
    """
    if name not in _DATASET_CACHE:
        if name not in DATASET_FILES:
            raise KeyError(f"Dataset '{name}' is not recognized. Valid: {list(DATASET_FILES.keys())}")
        file_path = DATA_PATH / DATASET_FILES[name]
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found at {file_path}")
        
        # Load dataset
        df = pd.read_csv(file_path)
        _DATASET_CACHE[name] = df
        
    return _DATASET_CACHE[name]


def Load_olist_datasets(include_geolocation: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Loads all core Olist datasets.
    Geolocation (62MB) is excluded by default for blazing-fast startup and memory efficiency.
    """
    keys = [
        "orders",
        "customers",
        "order_items",
        "products",
        "order_reviews",
        "order_payments",
        "sellers",
        "category_translation",
    ]
    if include_geolocation:
        keys.append("geolocation")

    for key in keys:
        if key not in _DATASET_CACHE:
            get_dataset(key)

    return {k: _DATASET_CACHE[k] for k in keys}


def clear_dataset_cache():
    """Clears cached dataframes (useful when uploading a new dataset)."""
    global _DATASET_CACHE
    _DATASET_CACHE.clear()
