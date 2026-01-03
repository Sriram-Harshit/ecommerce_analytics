from django.shortcuts import render
from django.http import HttpResponse
import csv

# ======================
# DATA LOADING
# ======================
from dashboard.services.default_dataset import Load_olist_datasets

# ======================
# ANALYTICS (KPIs + CHARTS + TIER-2)
# ======================
from dashboard.services.analytics import (
    calculate_total_orders,
    calculate_total_revenue,
    calculate_delayed_orders,
    calculate_average_review_score,
    calculate_repeat_customer_rate,
    orders_over_time,
    revenue_by_category,
    delivery_delay_distribution,
    calculate_aov_over_time,
    customer_segmentation,
    review_vs_delay,
    payment_method_analysis,
    build_retention_insight,
)

# ======================
# ML
# ======================
from dashboard.services.ml_models import (
    prepare_delay_dataset,
    train_delay_prediction_model,
)

# ======================
# TIER-4 DATA QUALITY
# ======================
from dashboard.services.dataOvervire import (
    dataset_summary,
    missing_values_report,
    duplicate_report,
    risk_highlights,
    order_items_integrity_check,
    customer_linkage_check,
)

# Load default Olist datasets ONCE
data = Load_olist_datasets()


# =========================================================
# DASHBOARD
# =========================================================
def dashboard_home(request):

    # ---------- KPIs ----------
    orders_count = calculate_total_orders(data["orders"])
    total_revenue = calculate_total_revenue(data["order_items"])
    delayed_orders = calculate_delayed_orders(data["orders"])
    avg_review = calculate_average_review_score(data["order_reviews"])
    repeat_rate = calculate_repeat_customer_rate(data["orders"], data["customers"])

    # ---------- Tier-1 Charts ----------
    orders_time_df = orders_over_time(data["orders"])

    revenue_df = revenue_by_category(
        data["order_items"],
        data["products"],
        data["category_translation"],
    )

    delay_dist = delivery_delay_distribution(data["orders"])

    aov_data = calculate_aov_over_time(
        data["orders"],
        data["order_items"],
    )

    # ---------- Tier-2 Analytics ----------
    segmentation_df = customer_segmentation(
        data["orders"],
        data["order_items"],
        data["customers"],
    )

    review_delay_df = review_vs_delay(
        data["orders"],
        data["order_reviews"],
    )

    payment_df = payment_method_analysis(
        data["order_payments"],
        data["order_items"],
    )

    retention_insight = build_retention_insight(
        repeat_rate=repeat_rate,
        delayed_orders=delayed_orders,
        total_orders=orders_count,
    )

    # ---------- Tier-4 Data Quality ----------
    summary = dataset_summary(data["orders"])
    missing = missing_values_report(data["orders"])
    duplicates = duplicate_report(data["orders"])
    risks = risk_highlights(data["orders"], data["order_reviews"])

    order_items_check = order_items_integrity_check(data["orders"], data["order_items"])

    customer_linkage = customer_linkage_check(data["orders"], data["customers"])

    # ---------- Context ----------
    context = {
        # KPIs
        "orders_count": orders_count,
        "total_revenue": round(total_revenue, 2),
        "delayed_orders": delayed_orders,
        "avg_review": avg_review,
        "repeat_rate": repeat_rate,
        # Charts
        "orders_time_data": orders_time_df.to_dict(orient="records"),
        "rev_cat_labels": revenue_df["product_category_name_english"].tolist(),
        "rev_cat_values": revenue_df["revenue"].tolist(),
        "delay_labels": list(delay_dist.keys()),
        "delay_values": list(delay_dist.values()),
        "aov_labels": aov_data["labels"],
        "aov_values": aov_data["values"],
        # Tier-2
        "customer_segments": segmentation_df.to_dict(orient="records"),
        "review_delay": review_delay_df.to_dict(orient="records"),
        "payment_methods": payment_df.to_dict(orient="records"),
        "retention_insight": retention_insight,
        # Tier-4
        "dataset_summary": summary,
        "missing_values": missing,
        "duplicates": duplicates,
        "risks": risks,
        "order_items_check": order_items_check,
        "customer_linkage": customer_linkage,
    }

    return render(request, "dashboard/pages/dashboard.html", context)


# =========================================================
# KPI EXPORT (CSV)
# =========================================================
def export_kpis(request):
    """
    Export KPI metrics as CSV
    """

    kpis = {
        "Total Orders": calculate_total_orders(data["orders"]),
        "Total Revenue": round(calculate_total_revenue(data["order_items"]), 2),
        "Delayed Orders": calculate_delayed_orders(data["orders"]),
        "Average Review Score": calculate_average_review_score(data["order_reviews"]),
        "Repeat Customer Rate (%)": round(
            calculate_repeat_customer_rate(data["orders"], data["customers"]),
            2,
        ),
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="kpi_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Metric", "Value"])

    for metric, value in kpis.items():
        writer.writerow([metric, value])

    return response


# =========================================================
# UPLOAD PAGE
# =========================================================
def upload_data(request):
    return render(request, "dashboard/pages/upload.html")


# =========================================================
# ML RESULTS
# =========================================================
def Ml_results(request):

    delay_df = prepare_delay_dataset(
        data["orders"],
        data["order_items"],
    )

    ml_results = train_delay_prediction_model(delay_df)

    context = {
        "total_orders": calculate_total_orders(data["orders"]),
        "total_revenue": round(calculate_total_revenue(data["order_items"]), 2),
        "delayed_orders": calculate_delayed_orders(data["orders"]),
        "avg_review": calculate_average_review_score(data["order_reviews"]),
        "ml": ml_results,
    }

    return render(request, "dashboard/pages/results.html", context)
