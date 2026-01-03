import pandas as pd

# =========================================================
# KPI FUNCTIONS
# =========================================================


def calculate_total_orders(orders_df: pd.DataFrame) -> int:
    """
    WHAT: Total number of unique orders
    WHY: Core business volume metric
    """
    return int(orders_df["order_id"].nunique())


def calculate_total_revenue(order_items_df: pd.DataFrame) -> float:
    """
    WHAT: Total revenue from all order items (price + freight)
    WHY: Measures gross sales value
    """
    return float(
        (order_items_df["price"] + order_items_df["freight_value"]).sum().round(2)
    )


def calculate_delayed_orders(orders_df: pd.DataFrame) -> int:
    """
    WHAT: Number of orders delivered after estimated delivery date
    WHY: Measures logistics performance
    """

    orders = orders_df.copy()

    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )
    orders["order_estimated_delivery_date"] = pd.to_datetime(
        orders["order_estimated_delivery_date"], errors="coerce"
    )

    orders = orders.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    delayed_orders = orders[
        orders["order_delivered_customer_date"]
        > orders["order_estimated_delivery_date"]
    ]

    return int(delayed_orders["order_id"].nunique())


def calculate_average_review_score(reviews_df: pd.DataFrame) -> float:
    """
    WHAT: Average customer review score
    WHY: Measures overall customer satisfaction
    """
    return float(reviews_df["review_score"].mean().round(2))


def calculate_repeat_customer_rate(
    orders_df: pd.DataFrame, customers_df: pd.DataFrame
) -> float:
    """
    WHAT: Percentage of customers who placed more than one order
    WHY: Measures customer retention

    NOTE:
    Uses customer_unique_id (real customer identifier)
    """

    orders_customers = orders_df.merge(
        customers_df[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )

    orders_per_customer = orders_customers.groupby("customer_unique_id")[
        "order_id"
    ].nunique()

    total_customers = int(orders_per_customer.shape[0])
    repeat_customers = int((orders_per_customer > 1).sum())

    if total_customers == 0:
        return 0.0

    return round((repeat_customers / total_customers) * 100, 2)


# =========================================================
# TIER-1 CHARTS
# =========================================================


def orders_over_time(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Orders per month
    WHY: Shows demand trend over time
    """

    df = orders_df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(
        df["order_purchase_timestamp"], errors="coerce"
    )

    result = (
        df.dropna(subset=["order_purchase_timestamp"])
        .groupby(
            [
                df["order_purchase_timestamp"].dt.year.rename("year"),
                df["order_purchase_timestamp"].dt.month.rename("month"),
            ]
        )
        .size()
        .reset_index(name="order_count")
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )

    return result


def revenue_by_category(
    order_items_df: pd.DataFrame,
    products_df: pd.DataFrame,
    translations_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    WHAT: Top product categories by revenue
    WHY: Identifies high-performing categories
    """

    df = order_items_df.merge(products_df, on="product_id", how="left").merge(
        translations_df, on="product_category_name", how="left"
    )

    revenue = (
        df.groupby("product_category_name_english", as_index=False)
        .agg(revenue=("price", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )

    revenue["revenue"] = revenue["revenue"].round(2)

    return revenue


def delivery_delay_distribution(orders_df: pd.DataFrame) -> dict:
    """
    WHAT: Distribution of early / on-time / delayed deliveries
    WHY: Visualizes logistics reliability
    """

    df = orders_df.copy()

    df["order_delivered_customer_date"] = pd.to_datetime(
        df["order_delivered_customer_date"], errors="coerce"
    )
    df["order_estimated_delivery_date"] = pd.to_datetime(
        df["order_estimated_delivery_date"], errors="coerce"
    )

    df = df.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    delay_days = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days

    return {
        "Early": int((delay_days < 0).sum()),
        "On Time": int((delay_days == 0).sum()),
        "Delayed": int((delay_days > 0).sum()),
    }


def calculate_aov_over_time(
    orders_df: pd.DataFrame, order_items_df: pd.DataFrame
) -> dict:
    """
    WHAT: Average Order Value (AOV) per month
    WHY: Shows spending behavior trends
    """

    orders = orders_df.copy()
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    revenue_per_order = order_items_df.groupby("order_id", as_index=False).agg(
        order_revenue=("price", "sum")
    )

    merged = orders.merge(revenue_per_order, on="order_id", how="inner")

    merged["month"] = merged["order_purchase_timestamp"].dt.to_period("M").astype(str)

    monthly = merged.groupby("month", as_index=False).agg(
        total_revenue=("order_revenue", "sum"),
        total_orders=("order_id", "nunique"),
    )

    monthly["aov"] = (monthly["total_revenue"] / monthly["total_orders"]).round(2)

    return {
        "labels": monthly["month"].tolist(),
        "values": monthly["aov"].tolist(),
    }


# =========================================================
# TIER-2 ANALYTICS (NO ML)
# =========================================================


def customer_segmentation(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    WHAT: Segment customers by purchase frequency
    WHY: Understand retention and revenue concentration
    """

    orders_customers = orders_df.merge(
        customers_df[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )

    order_counts = (
        orders_customers.groupby("customer_unique_id")["order_id"]
        .nunique()
        .reset_index(name="order_count")
    )

    def segment(count: int) -> str:
        if count == 1:
            return "New"
        elif count <= 2:
            return "Returning"
        return "Loyal"

    order_counts["segment"] = order_counts["order_count"].apply(segment)

    revenue_per_order = order_items_df.groupby("order_id", as_index=False).agg(
        order_revenue=("price", "sum")
    )

    merged = orders_customers.merge(revenue_per_order, on="order_id", how="left").merge(
        order_counts, on="customer_unique_id", how="left"
    )

    result = merged.groupby("segment", as_index=False).agg(
        customers=("customer_unique_id", "nunique"),
        orders=("order_id", "nunique"),
        revenue=("order_revenue", "sum"),
    )

    result["revenue"] = result["revenue"].round(2)

    return result


def review_vs_delay(orders_df: pd.DataFrame, reviews_df: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Compare review scores for on-time vs delayed orders
    WHY: Measures customer experience impact of delivery delays
    """

    orders = orders_df.copy()

    orders["order_delivered_customer_date"] = pd.to_datetime(
        orders["order_delivered_customer_date"], errors="coerce"
    )
    orders["order_estimated_delivery_date"] = pd.to_datetime(
        orders["order_estimated_delivery_date"], errors="coerce"
    )

    orders = orders.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    orders["is_delayed"] = (
        orders["order_delivered_customer_date"]
        > orders["order_estimated_delivery_date"]
    )

    merged = orders.merge(
        reviews_df[["order_id", "review_score"]],
        on="order_id",
        how="inner",
    )

    result = merged.groupby("is_delayed", as_index=False).agg(
        avg_review=("review_score", "mean"),
        orders=("order_id", "nunique"),
    )

    result["delivery_status"] = result["is_delayed"].map(
        {False: "On-Time", True: "Delayed"}
    )
    result["avg_review"] = result["avg_review"].round(2)

    return (
        result[["delivery_status", "avg_review", "orders"]]
        .sort_values("delivery_status")
        .reset_index(drop=True)
    )


def payment_method_analysis(
    payments_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    WHAT:
    Orders and revenue by payment method

    WHY:
    Understand customer payment preferences and revenue contribution
    """

    # Order-level revenue
    order_revenue = order_items_df.groupby("order_id", as_index=False).agg(
        order_revenue=("price", "sum")
    )

    # Merge
    merged = payments_df.merge(order_revenue, on="order_id", how="left")
    merged["order_revenue"] = merged["order_revenue"].fillna(0)

    # Aggregate
    result = merged.groupby("payment_type", as_index=False).agg(
        orders=("order_id", "nunique"),
        revenue=("order_revenue", "sum"),
    )

    result["payment_type"] = (
        result["payment_type"].str.replace("_", " ", regex=False).str.title()
    )

    # Optional: clean ugly category
    result["payment_type"] = result["payment_type"].replace(
        {"Not Defined": "Other / Unknown"}
    )

    result["revenue"] = result["revenue"].round(2)

    return result.sort_values("revenue", ascending=False).reset_index(drop=True)


def build_retention_insight(
    repeat_rate: float,
    delayed_orders: int,
    total_orders: int,
) -> dict:
    """
    Advanced retention insight engine using multiple signals.
    Threshold bands: 0–25–50–75–100
    """

    # -------------------------
    # Core metrics
    # -------------------------
    delay_rate = (delayed_orders / total_orders) * 100 if total_orders else 0

    # -------------------------
    # Retention classification
    # -------------------------
    if repeat_rate < 25:
        retention_band = "low"
        severity_score = 3
    elif repeat_rate < 50:
        retention_band = "moderate"
        severity_score = 2
    elif repeat_rate < 75:
        retention_band = "strong"
        severity_score = 1
    else:
        retention_band = "very strong"
        severity_score = 0

    # -------------------------
    # Primary driver analysis
    # -------------------------
    if delay_rate >= 50:
        primary_driver = "logistics reliability"
        driver_message = (
            "A high delivery delay rate suggests logistics performance is a major"
            " contributor to low repeat purchases."
        )
    elif delay_rate >= 25:
        primary_driver = "delivery experience"
        driver_message = (
            "Delivery delays affect a significant portion of orders and may be"
            " impacting customer satisfaction."
        )
    else:
        primary_driver = "post-purchase engagement"
        driver_message = (
            "Delivery performance appears stable, indicating that post-purchase"
            " engagement and communication may be limiting retention."
        )

    # -------------------------
    # Executive summary text
    # -------------------------
    summary_message = (
        f"Customer retention is {retention_band}, with only "
        f"{round(repeat_rate, 2)}% of customers placing repeat orders."
    )

    # -------------------------
    # Recommendation logic
    # -------------------------
    if severity_score >= 3:
        recommendation = (
            "Retention is critically low. Prioritizing improvements in delivery"
            " reliability and post-purchase experience could significantly improve"
            " repeat purchases."
        )
    elif severity_score == 2:
        recommendation = (
            "Retention shows early potential. Targeted improvements in customer"
            " experience could help convert first-time buyers into repeat customers."
        )
    else:
        recommendation = (
            "Retention performance is healthy. Continued focus on customer experience"
            " can help sustain repeat purchasing behavior."
        )

    return {
        "repeat_rate": round(repeat_rate, 2),
        "delay_rate": round(delay_rate, 2),
        "retention_band": retention_band,
        "severity_score": severity_score,
        "primary_driver": primary_driver,
        "summary_message": summary_message,
        "driver_message": driver_message,
        "recommendation": recommendation,
    }
