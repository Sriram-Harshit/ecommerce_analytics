import pandas as pd
import numpy as np
from typing import Dict, Any, List

# =========================================================
# KPI FUNCTIONS
# =========================================================

def calculate_total_orders(orders_df: pd.DataFrame) -> int:
    """Total unique orders placed in the system."""
    return int(orders_df["order_id"].nunique())


def calculate_total_revenue(order_items_df: pd.DataFrame, include_freight: bool = True) -> float:
    """
    Total gross revenue (Product Price + Freight Value if include_freight else Product Price).
    """
    if include_freight:
        return float((order_items_df["price"] + order_items_df["freight_value"]).sum().round(2))
    return float(order_items_df["price"].sum().round(2))


def calculate_delayed_orders(orders_df: pd.DataFrame) -> int:
    """
    Calculates delayed deliveries using calendar date comparison.
    An order is delayed if actual delivery date is strictly past the estimated delivery date.
    Delivery on the estimated date is counted as On-Time.
    """
    orders = orders_df.copy()
    orders["delivered"] = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")
    orders["estimated"] = pd.to_datetime(orders["order_estimated_delivery_date"], errors="coerce")

    valid = orders.dropna(subset=["delivered", "estimated"])
    delayed = valid[valid["delivered"].dt.date > valid["estimated"].dt.date]

    return int(delayed["order_id"].nunique())


def calculate_average_review_score(reviews_df: pd.DataFrame) -> float:
    """Average customer satisfaction review score (1.0 - 5.0)."""
    return float(reviews_df["review_score"].mean().round(2))


def calculate_repeat_customer_rate(
    orders_df: pd.DataFrame, customers_df: pd.DataFrame
) -> float:
    """
    Percentage of unique customers with more than 1 purchase.
    Uses 'customer_unique_id' to track true returning buyers.
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
# TRENDS & CHARTS ANALYTICS
# =========================================================

def orders_over_time(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates order counts by Year and Month."""
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
    top_n: int = 10,
) -> pd.DataFrame:
    """Top product categories by gross product revenue."""
    df = order_items_df.merge(products_df, on="product_id", how="left").merge(
        translations_df, on="product_category_name", how="left"
    )

    # Fallback to Portuguese name if translation missing
    df["category"] = df["product_category_name_english"].fillna(df["product_category_name"]).fillna("Uncategorized")

    revenue = (
        df.groupby("category", as_index=False)
        .agg(
            revenue=("price", "sum"),
            items_sold=("order_item_id", "count"),
        )
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )

    revenue["revenue"] = revenue["revenue"].round(2)
    return revenue


def delivery_delay_distribution(orders_df: pd.DataFrame) -> Dict[str, int]:
    """
    Accurate early / on-time / delayed breakdown matching KPI definition.
    - Early: Delivered before the estimated delivery day.
    - On Time: Delivered on the estimated delivery day.
    - Delayed: Delivered after the estimated delivery day.
    """
    df = orders_df.copy()
    df["delivered"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
    df["estimated"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")

    valid = df.dropna(subset=["delivered", "estimated"])

    is_early = valid["delivered"].dt.date < valid["estimated"].dt.date
    is_ontime = valid["delivered"].dt.date == valid["estimated"].dt.date
    is_delayed = valid["delivered"].dt.date > valid["estimated"].dt.date

    return {
        "Early": int(is_early.sum()),
        "On Time": int(is_ontime.sum()),
        "Delayed": int(is_delayed.sum()),
    }


def calculate_aov_over_time(
    orders_df: pd.DataFrame, order_items_df: pd.DataFrame
) -> Dict[str, List[Any]]:
    """Average Order Value (AOV) monthly timeline."""
    orders = orders_df.copy()
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )

    revenue_per_order = order_items_df.groupby("order_id", as_index=False).agg(
        order_revenue=("price", "sum")
    )

    merged = orders.merge(revenue_per_order, on="order_id", how="inner")
    merged["month"] = merged["order_purchase_timestamp"].dt.to_period("M").astype(str)

    monthly = (
        merged.groupby("month", as_index=False)
        .agg(
            total_revenue=("order_revenue", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .sort_values("month")
    )

    monthly["aov"] = (monthly["total_revenue"] / monthly["total_orders"]).round(2)

    return {
        "labels": monthly["month"].tolist(),
        "values": monthly["aov"].tolist(),
    }


def top_sellers_ranking(
    order_items_df: pd.DataFrame,
    sellers_df: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """Returns top performing sellers by revenue and volume."""
    seller_stats = (
        order_items_df.groupby("seller_id", as_index=False)
        .agg(
            revenue=("price", "sum"),
            orders=("order_id", "nunique"),
            items=("order_item_id", "count"),
        )
        .merge(sellers_df[["seller_id", "seller_city", "seller_state"]], on="seller_id", how="left")
        .sort_values("revenue", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    seller_stats["revenue"] = seller_stats["revenue"].round(2)
    seller_stats["short_id"] = seller_stats["seller_id"].apply(lambda s: f"Seller #{s[:6].upper()}")
    return seller_stats


# =========================================================
# SEGMENTATION, EXPERIENCE & RETENTION
# =========================================================

def customer_segmentation(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> pd.DataFrame:
    """Segments customers into New, Returning, and Loyal cohorts."""
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
            return "New (1 Order)"
        elif count == 2:
            return "Returning (2 Orders)"
        return "Loyal (3+ Orders)"

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
    result["aov"] = (result["revenue"] / result["orders"]).round(2)

    # Sort in logical cohort order
    cohort_order = {"New (1 Order)": 1, "Returning (2 Orders)": 2, "Loyal (3+ Orders)": 3}
    result["sort_key"] = result["segment"].map(cohort_order)
    result = result.sort_values("sort_key").drop(columns=["sort_key"]).reset_index(drop=True)

    return result


def review_vs_delay(orders_df: pd.DataFrame, reviews_df: pd.DataFrame) -> pd.DataFrame:
    """Demonstrates customer rating drop when delivery is delayed."""
    orders = orders_df.copy()
    orders["delivered"] = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")
    orders["estimated"] = pd.to_datetime(orders["order_estimated_delivery_date"], errors="coerce")

    valid = orders.dropna(subset=["delivered", "estimated"]).copy()
    valid["is_delayed"] = valid["delivered"].dt.date > valid["estimated"].dt.date

    merged = valid.merge(
        reviews_df[["order_id", "review_score"]],
        on="order_id",
        how="inner",
    )

    result = merged.groupby("is_delayed", as_index=False).agg(
        avg_review=("review_score", "mean"),
        orders=("order_id", "nunique"),
    )

    result["delivery_status"] = result["is_delayed"].map(
        {False: "On-Time Deliveries", True: "Delayed Deliveries"}
    )
    result["avg_review"] = result["avg_review"].round(2)

    return (
        result[["delivery_status", "avg_review", "orders"]]
        .sort_values("delivery_status", ascending=False)
        .reset_index(drop=True)
    )


def payment_method_analysis(payments_df: pd.DataFrame) -> pd.DataFrame:
    """Accurately calculates revenue and order share per payment method without double-counting."""
    result = payments_df.groupby("payment_type", as_index=False).agg(
        orders=("order_id", "nunique"),
        revenue=("payment_value", "sum"),
    )

    result["payment_type"] = (
        result["payment_type"].str.replace("_", " ", regex=False).str.title()
    )
    result["payment_type"] = result["payment_type"].replace(
        {"Not Defined": "Other / Unknown"}
    )
    result["revenue"] = result["revenue"].round(2)

    total_rev = result["revenue"].sum()
    result["share_percent"] = ((result["revenue"] / total_rev) * 100).round(1)

    return result.sort_values("revenue", ascending=False).reset_index(drop=True)


def build_retention_insight(
    repeat_rate: float,
    delayed_orders: int,
    delivered_orders: int,
) -> Dict[str, Any]:
    """Actionable intelligence engine evaluating retention against delivery performance."""
    delay_rate = (delayed_orders / delivered_orders) * 100 if delivered_orders else 0

    if repeat_rate < 5:
        retention_band = "Critical"
        severity_score = 3
    elif repeat_rate < 15:
        retention_band = "Moderate"
        severity_score = 2
    else:
        retention_band = "Strong"
        severity_score = 1

    if delay_rate > 10:
        primary_driver = "Logistics Friction"
        driver_message = (
            f"Delivery delay rate stands at {round(delay_rate, 1)}%. Shipping bottlenecks "
            "are a primary cause of suppressed second-order conversion."
        )
    elif delay_rate > 5:
        primary_driver = "Fulfillment Variability"
        driver_message = (
            f"{round(delay_rate, 1)}% of orders missed delivery deadlines, creating negative "
            "first impressions that lower customer re-engagement."
        )
    else:
        primary_driver = "Post-Purchase Lifecycle"
        driver_message = (
            "Fulfillment reliability is solid. Low repeat purchase rates point to missed "
            "post-purchase email marketing and loyalty incentives."
        )

    summary_message = (
        f"Customer retention is currently at {round(repeat_rate, 2)}% repeat customer rate."
    )

    if severity_score >= 3:
        recommendation = (
            "Establish automated re-engagement flows within 14 days of successful delivery, "
            "and prioritize carrier SLAs in high-delay regions to protect brand loyalty."
        )
    elif severity_score == 2:
        recommendation = (
            "Target first-time buyers with category-specific cross-sell discounts and VIP incentives "
            "to convert them into high-LTV returning customers."
        )
    else:
        recommendation = (
            "Retention performance is exemplary. Scale current loyalty programs to expand average order frequency."
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


# =========================================================
# REGIONAL SALES BY STATE (GEOGRAPHIC BREAKDOWN)
# =========================================================

STATE_NAMES = {
    "SP": "São Paulo",
    "RJ": "Rio de Janeiro",
    "MG": "Minas Gerais",
    "RS": "Rio Grande do Sul",
    "PR": "Paraná",
    "SC": "Santa Catarina",
    "BA": "Bahia",
    "DF": "Distrito Federal",
    "GO": "Goiás",
    "ES": "Espírito Santo",
    "PE": "Pernambuco",
    "CE": "Ceará",
    "PA": "Pará",
    "MT": "Mato Grosso",
    "MA": "Maranhão",
    "MS": "Mato Grosso do Sul",
    "PB": "Paraíba",
    "PI": "Piauí",
    "RN": "Rio Grande do Norte",
    "AL": "Alagoas",
    "SE": "Sergipe",
    "TO": "Tocantins",
    "RO": "Rondônia",
    "AM": "Amazonas",
    "AC": "Acre",
    "AP": "Amapá",
    "RR": "Roraima",
}


def sales_by_state(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    top_n: int = 6,
) -> pd.DataFrame:
    """
    Calculates top regional markets by order count and gross sales volume.
    Maps state codes to official full state names and provides market share %.
    """
    rev = order_items_df.groupby("order_id", as_index=False).agg(revenue=("price", "sum"))
    merged = (
        orders_df[["order_id", "customer_id"]]
        .merge(customers_df[["customer_id", "customer_state"]], on="customer_id")
        .merge(rev, on="order_id")
    )

    total_revenue = merged["revenue"].sum()
    states = (
        merged.groupby("customer_state", as_index=False)
        .agg(orders=("order_id", "nunique"), revenue=("revenue", "sum"))
        .sort_values("revenue", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    states["revenue"] = states["revenue"].round(2)
    states["state_name"] = states["customer_state"].map(STATE_NAMES).fillna(states["customer_state"])
    states["share_percent"] = ((states["revenue"] / total_revenue) * 100).round(1) if total_revenue > 0 else 0

    return states

