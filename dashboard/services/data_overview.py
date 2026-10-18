import pandas as pd
from typing import Dict, Any, List

# =========================================================
# DATA INTEGRITY & AUDIT ENGINE
# =========================================================

def dataset_summary(df: pd.DataFrame) -> Dict[str, int]:
    """Basic dataset dimensional stats."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }


def missing_values_report(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detailed missing values audit with column name, null count, and null percentage."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    total_rows = len(df)

    report = []
    for col, count in missing.items():
        pct = round((count / total_rows) * 100, 2)
        report.append({
            "column": col,
            "missing_count": int(count),
            "missing_percent": pct,
            "status": "warning" if pct > 5 else "info",
        })

    return sorted(report, key=lambda x: x["missing_count"], reverse=True)


def duplicate_report(df: pd.DataFrame) -> Dict[str, int]:
    """Detect duplicate records across all columns."""
    return {"duplicate_rows": int(df.duplicated().sum())}


def order_items_integrity_check(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Detects orphaned orders that have no corresponding items in order_items."""
    orders_with_items = set(order_items_df["order_id"].unique())
    all_orders = set(orders_df["order_id"].unique())

    missing_items_orders = all_orders - orders_with_items
    total_orders = len(all_orders)
    pct = round((len(missing_items_orders) / total_orders) * 100, 2) if total_orders else 0

    return {
        "orders_without_items": len(missing_items_orders),
        "percentage": pct,
        "is_healthy": len(missing_items_orders) < (0.01 * total_orders),
    }


def customer_linkage_check(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Detects broken foreign key mapping between orders and customers."""
    merged = orders_df.merge(
        customers_df[["customer_id"]],
        on="customer_id",
        how="left",
        indicator=True,
    )

    missing_customers = int((merged["_merge"] == "left_only").sum())

    return {
        "orders_without_customer": missing_customers,
        "is_healthy": missing_customers == 0,
    }


def risk_highlights(
    orders_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    High-level operational health indicators:
    - Delivery delay rate among delivered orders
    - Dissatisfied review percentage (rating <= 2 stars)
    """
    orders = orders_df.copy()
    orders["delivered"] = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")
    orders["estimated"] = pd.to_datetime(orders["order_estimated_delivery_date"], errors="coerce")

    delivered = orders.dropna(subset=["delivered", "estimated"])
    delayed_orders = delivered[delivered["delivered"].dt.date > delivered["estimated"].dt.date]

    delay_rate = (len(delayed_orders) / len(delivered)) * 100 if len(delivered) > 0 else 0
    low_review_rate = ((reviews_df["review_score"] <= 2).mean() * 100) if not reviews_df.empty else 0

    return {
        "delay_rate_percent": round(delay_rate, 2),
        "low_review_percent": round(low_review_rate, 2),
        "delay_risk_flag": delay_rate > 10.0,
        "review_risk_flag": low_review_rate > 15.0,
    }


def calculate_data_health_score(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Synthesizes multiple data quality dimensions into an overall Health Score (0 - 100%).
    """
    # 1. Duplicates penalty
    dup_orders = int(orders_df.duplicated().sum())
    dup_penalty = 5.0 if dup_orders > 0 else 0.0

    # 2. Foreign Key Linkage penalty
    linkage = customer_linkage_check(orders_df, customers_df)
    linkage_penalty = 10.0 if not linkage["is_healthy"] else 0.0

    # 3. Orphaned Items penalty
    items_check = order_items_integrity_check(orders_df, order_items_df)
    items_penalty = min(items_check["percentage"] * 2, 10.0)

    # 4. Critical Missing Values penalty in primary keys
    pk_nulls = orders_df["order_id"].isnull().sum() + customers_df["customer_id"].isnull().sum()
    pk_penalty = 20.0 if pk_nulls > 0 else 0.0

    health_score = round(max(0.0, 100.0 - dup_penalty - linkage_penalty - items_penalty - pk_penalty), 1)

    return {
        "health_score": health_score,
        "status": "Optimal" if health_score >= 95 else "Attention Needed",
        "audited_tables": 4,
        "total_records": len(orders_df) + len(order_items_df) + len(customers_df) + len(reviews_df),
    }
