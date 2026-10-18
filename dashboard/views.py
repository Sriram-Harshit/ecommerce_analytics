import csv
import json
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# ======================
# DATA SERVICES
# ======================
from dashboard.services.default_dataset import Load_olist_datasets, get_dataset, clear_dataset_cache

# ======================
# ANALYTICS ENGINE
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
    top_sellers_ranking,
    customer_segmentation,
    review_vs_delay,
    payment_method_analysis,
    build_retention_insight,
    sales_by_state,
)

# ======================
# MACHINE LEARNING
# ======================
from dashboard.services.ml_models import (
    prepare_delay_dataset,
    train_delay_prediction_model,
    predict_single_order,
)

# ======================
# DATA QUALITY & AUDIT
# ======================
from dashboard.services.data_overview import (
    dataset_summary,
    missing_values_report,
    duplicate_report,
    risk_highlights,
    order_items_integrity_check,
    customer_linkage_check,
    calculate_data_health_score,
)

# Global in-memory cache for computed dashboard analytics to make page loads sub-second
_DASHBOARD_CACHE = {}


def _get_dashboard_analytics():
    """Calculates or retrieves cached analytics payload."""
    global _DASHBOARD_CACHE
    if "context" in _DASHBOARD_CACHE:
        return _DASHBOARD_CACHE["context"]

    # Load core datasets (geolocation excluded for speed)
    data = Load_olist_datasets()

    orders_count = calculate_total_orders(data["orders"])
    gross_revenue = calculate_total_revenue(data["order_items"], include_freight=True)
    product_revenue = calculate_total_revenue(data["order_items"], include_freight=False)
    delayed_orders = calculate_delayed_orders(data["orders"])
    avg_review = calculate_average_review_score(data["order_reviews"])
    repeat_rate = calculate_repeat_customer_rate(data["orders"], data["customers"])

    # Trend & Category Charts
    orders_time_df = orders_over_time(data["orders"])
    revenue_df = revenue_by_category(
        data["order_items"],
        data["products"],
        data["category_translation"],
        top_n=10,
    )
    delay_dist = delivery_delay_distribution(data["orders"])
    aov_data = calculate_aov_over_time(data["orders"], data["order_items"])

    # Top Sellers
    top_sellers_df = top_sellers_ranking(data["order_items"], data["sellers"], top_n=5)

    # Regional Sales by State
    states_df = sales_by_state(data["orders"], data["customers"], data["order_items"], top_n=6)

    # Advanced Cohort & Experience Analytics
    segmentation_df = customer_segmentation(
        data["orders"],
        data["order_items"],
        data["customers"],
    )
    review_delay_df = review_vs_delay(data["orders"], data["order_reviews"])
    payment_df = payment_method_analysis(data["order_payments"])

    # Delivered orders count for consistent delay rate denominator
    delivered_count = sum(delay_dist.values())
    retention_insight = build_retention_insight(
        repeat_rate=repeat_rate,
        delayed_orders=delayed_orders,
        delivered_orders=delivered_count,
    )

    # Data Quality summary
    summary = dataset_summary(data["orders"])
    missing = missing_values_report(data["orders"])
    duplicates = duplicate_report(data["orders"])
    risks = risk_highlights(data["orders"], data["order_reviews"])
    order_items_check = order_items_integrity_check(data["orders"], data["order_items"])
    customer_linkage = customer_linkage_check(data["orders"], data["customers"])
    health_score_data = calculate_data_health_score(
        data["orders"], data["order_items"], data["customers"], data["order_reviews"]
    )

    context = {
        # Core KPIs
        "orders_count": orders_count,
        "gross_revenue": gross_revenue,
        "product_revenue": product_revenue,
        "delayed_orders": delayed_orders,
        "avg_review": avg_review,
        "repeat_rate": repeat_rate,
        # Visual Analytics
        "orders_time_data": orders_time_df.to_dict(orient="records"),
        "rev_cat_labels": revenue_df["category"].tolist(),
        "rev_cat_values": revenue_df["revenue"].tolist(),
        "delay_labels": list(delay_dist.keys()),
        "delay_values": list(delay_dist.values()),
        "aov_labels": aov_data["labels"],
        "aov_values": aov_data["values"],
        "top_sellers": top_sellers_df.to_dict(orient="records"),
        "top_sellers_labels": top_sellers_df["short_id"].tolist(),
        "top_sellers_values": top_sellers_df["revenue"].tolist(),
        "state_sales": states_df.to_dict(orient="records"),
        "state_labels": states_df["state_name"].tolist(),
        "state_values": states_df["revenue"].tolist(),
        # Cohorts & Insights
        "customer_segments": segmentation_df.to_dict(orient="records"),
        "review_delay": review_delay_df.to_dict(orient="records"),
        "payment_methods": payment_df.to_dict(orient="records"),
        "retention_insight": retention_insight,
        # Data Quality
        "dataset_summary": summary,
        "missing_values": missing,
        "duplicates": duplicates,
        "risks": risks,
        "order_items_check": order_items_check,
        "customer_linkage": customer_linkage,
        "health_score": health_score_data,
    }

    _DASHBOARD_CACHE["context"] = context
    return context


# =========================================================
# 1. EXECUTIVE DASHBOARD VIEW
# =========================================================
def dashboard_home(request):
    """Renders the revamped Executive Business Analytics Dashboard."""
    context = _get_dashboard_analytics()
    return render(request, "dashboard/pages/dashboard.html", context)


# =========================================================
# 2. ML PREDICTIONS & SIMULATOR VIEW
# =========================================================
def ml_results(request):
    """Renders the Machine Learning Delay Prediction & Simulator page."""
    data = Load_olist_datasets()

    delay_df = prepare_delay_dataset(
        data["orders"],
        data["order_items"],
        data["order_payments"],
    )

    ml_metrics = train_delay_prediction_model(delay_df)

    context = {
        "ml": ml_metrics,
        "default_sample": {
            "freight_value": 24.50,
            "price": 149.90,
            "item_count": 2,
            "installments": 3,
        },
    }

    return render(request, "dashboard/pages/results.html", context)


# Backward compatibility alias for any existing reference
Ml_results = ml_results


# =========================================================
# 3. DEDICATED DATA QUALITY & HEALTH AUDIT VIEW
# =========================================================
def data_quality_view(request):
    """Renders the dedicated Data Quality and Pipeline Integrity report."""
    context = _get_dashboard_analytics()
    return render(request, "dashboard/pages/data_quality.html", context)


# =========================================================
# 4. FUNCTIONAL DATASET UPLOAD VIEW
# =========================================================
def upload_data(request):
    """
    Handles CSV dataset upload with schema validation, missing value detection,
    and preview generation.
    """
    upload_result = None

    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        file_name = uploaded_file.name

        if not file_name.endswith(".csv"):
            upload_result = {
                "success": False,
                "error": "Invalid file format. Please upload a standard comma-separated .csv file.",
            }
        else:
            try:
                # Read uploaded CSV
                df = pd.read_csv(uploaded_file)
                total_rows = len(df)
                total_cols = len(df.columns)
                columns_list = df.columns.tolist()

                # Missing values count
                missing_counts = df.isnull().sum()
                missing_dict = missing_counts[missing_counts > 0].to_dict()

                # Preview first 5 rows
                preview_records = df.head(5).fillna("-").to_dict(orient="records")
                preview_rows = df.head(5).fillna("-").values.tolist()

                upload_result = {
                    "success": True,
                    "file_name": file_name,
                    "rows": total_rows,
                    "columns": total_cols,
                    "columns_list": columns_list,
                    "missing_counts": missing_dict,
                    "preview": preview_records,
                    "preview_rows": preview_rows,
                    "duplicate_count": int(df.duplicated().sum()),
                }
            except Exception as e:
                upload_result = {
                    "success": False,
                    "error": f"Failed to parse CSV file: {str(e)}",
                }

    return render(request, "dashboard/pages/upload.html", {"upload_result": upload_result})


# =========================================================
# 5. KPI REPORT CSV EXPORT
# =========================================================
def export_kpis(request):
    """Exports structured business KPIs and audit summary as a downloadable CSV."""
    analytics = _get_dashboard_analytics()

    kpis = [
        ("EXECUTIVE METRIC", "VALUE"),
        ("Total Unique Orders", analytics["orders_count"]),
        ("Gross Merchandise Value (GMV R$)", f"R$ {analytics['gross_revenue']:,.2f}"),
        ("Net Product Sales (R$)", f"R$ {analytics['product_revenue']:,.2f}"),
        ("Delayed Deliveries", analytics["delayed_orders"]),
        ("Average Customer Review Score", f"{analytics['avg_review']} / 5.0"),
        ("Repeat Customer Rate (%)", f"{analytics['repeat_rate']}%"),
        ("Data Quality Health Score", f"{analytics['health_score']['health_score']}%"),
        ("Total Audited Records", analytics["health_score"]["total_records"]),
        ("Delivery Delay Risk Level", "Elevated" if analytics["risks"]["delay_risk_flag"] else "Normal"),
    ]

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="olist_ecommerce_kpi_report.csv"'

    writer = csv.writer(response)
    for row in kpis:
        writer.writerow(row)

    return response


# =========================================================
# 6. REST API ENDPOINTS
# =========================================================
@require_http_methods(["GET"])
def api_kpis(request):
    """REST API endpoint returning core business KPIs as JSON."""
    analytics = _get_dashboard_analytics()
    payload = {
        "orders_count": analytics["orders_count"],
        "gross_revenue": analytics["gross_revenue"],
        "product_revenue": analytics["product_revenue"],
        "delayed_orders": analytics["delayed_orders"],
        "avg_review": analytics["avg_review"],
        "repeat_rate": analytics["repeat_rate"],
        "health_score": analytics["health_score"]["health_score"],
    }
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["POST"])
def api_predict_delay(request):
    """
    REST API endpoint for real-time ML delay probability inference.
    Accepts JSON body: {freight_value, price, item_count, installments}
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        freight_value = float(data.get("freight_value", 20.0))
        price = float(data.get("price", 100.0))
        item_count = int(data.get("item_count", 1))
        installments = int(data.get("installments", 1))

        # Ensure model is initialized
        _get_dashboard_analytics()
        ml_data = Load_olist_datasets()
        delay_df = prepare_delay_dataset(ml_data["orders"], ml_data["order_items"], ml_data["order_payments"])
        train_delay_prediction_model(delay_df)

        prediction = predict_single_order(
            freight_value=freight_value,
            price=price,
            item_count=item_count,
            installments=installments,
        )
        return JsonResponse(prediction)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
