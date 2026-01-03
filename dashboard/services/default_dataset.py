import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "data" / "default"


def Load_olist_datasets():
    return {
        "orders": pd.read_csv(DATA_PATH / "olist_orders_dataset.csv"),
        "customers": pd.read_csv(DATA_PATH / "olist_customers_dataset.csv"),
        "order_items": pd.read_csv(DATA_PATH / "olist_order_items_dataset.csv"),
        "products": pd.read_csv(DATA_PATH / "olist_products_dataset.csv"),
        "order_reviews": pd.read_csv(DATA_PATH / "olist_order_reviews_dataset.csv"),
        "order_payments": pd.read_csv(DATA_PATH / "olist_order_payments_dataset.csv"),
        "sellers": pd.read_csv(DATA_PATH / "olist_sellers_dataset.csv"),
        "category_translation": pd.read_csv(
            DATA_PATH / "product_category_name_translation.csv"
        ),
        "geolocation": pd.read_csv(DATA_PATH / "olist_geolocation_dataset.csv"),
    }
