import pandas as pd

# =========================================================
# TIER-4: DATA QUALITY & OPERATIONAL INSIGHTS
# =========================================================


def dataset_summary(df: pd.DataFrame) -> dict:
    """
    WHAT:
    Basic dataset overview

    WHY:
    Shows data engineering maturity
    """
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
    }


def missing_values_report(df: pd.DataFrame) -> dict:
    """
    WHAT:
    Count missing values per column

    WHY:
    Detects incomplete data
    """
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    return missing.astype(int).to_dict()


def duplicate_report(df: pd.DataFrame) -> dict:
    """
    WHAT:
    Detect duplicate rows

    WHY:
    Prevents double counting & dirty analytics
    """
    return {"duplicate_rows": int(df.duplicated().sum())}


def order_items_integrity_check(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> dict:
    """
    WHAT:
    Check orders that have no associated order items

    WHY:
    Revenue integrity & broken joins detection
    """

    orders_with_items = set(order_items_df["order_id"].unique())
    all_orders = set(orders_df["order_id"].unique())

    missing_items_orders = all_orders - orders_with_items

    return {"orders_without_items": len(missing_items_orders)}


def customer_linkage_check(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> dict:
    """
    WHAT:
    Check orders missing customer mapping

    WHY:
    Detect broken foreign-key relationships
    """

    merged = orders_df.merge(
        customers_df[["customer_id"]],
        on="customer_id",
        how="left",
        indicator=True,
    )

    missing_customers = (merged["_merge"] == "left_only").sum()

    return {"orders_without_customer": int(missing_customers)}


def risk_highlights(
    orders_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> dict:
    """
    WHAT:
    High-level operational risk indicators

    WHY:
    Dashboards should highlight problems, not raw data
    """

    orders = orders_df.copy()

    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )
    orders["order_estimated_delivery_date"] = pd.to_datetime(
        orders["order_estimated_delivery_date"], errors="coerce"
    )

    delivered = orders.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    delayed_orders = delivered[
        delivered["order_delivered_customer_date"]
        > delivered["order_estimated_delivery_date"]
    ]

    delay_rate = (
        (len(delayed_orders) / len(delivered)) * 100 if len(delivered) > 0 else 0
    )

    low_review_rate = (
        (reviews_df["review_score"] <= 2).mean() * 100 if not reviews_df.empty else 0
    )

    return {
        "delay_rate_percent": round(delay_rate, 2),
        "low_review_percent": round(low_review_rate, 2),
        "delay_risk_flag": delay_rate > 20,
        "review_risk_flag": low_review_rate > 15,
    }


def export_kpis(kpi_dict: dict) -> pd.DataFrame:
    """
    WHAT:
    Convert KPI dictionary into exportable table

    WHY:
    Real dashboards allow exports
    """
    return pd.DataFrame(
        [{"Metric": key, "Value": value} for key, value in kpi_dict.items()]
    )
