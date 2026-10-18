import json
import pandas as pd
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from dashboard.services.analytics import (
    calculate_total_orders,
    calculate_total_revenue,
    calculate_delayed_orders,
    calculate_average_review_score,
    calculate_repeat_customer_rate,
    delivery_delay_distribution,
    payment_method_analysis,
    sales_by_state,
    build_retention_insight,
)
from dashboard.services.data_overview import (
    dataset_summary,
    missing_values_report,
    duplicate_report,
    customer_linkage_check,
    calculate_data_health_score,
)
from dashboard.services.ml_models import (
    prepare_delay_dataset,
    train_delay_prediction_model,
    predict_single_order,
)


class AnalyticsServiceUnitTests(TestCase):
    """Unit tests for core e-commerce analytical calculations."""

    def setUp(self):
        self.orders_df = pd.DataFrame({
            "order_id": ["o1", "o2", "o3"],
            "customer_id": ["c1", "c2", "c1"],
            "order_delivered_customer_date": [
                "2018-05-10 14:00:00",
                "2018-06-12 10:00:00",
                "2018-07-01 09:00:00",
            ],
            "order_estimated_delivery_date": [
                "2018-05-10 00:00:00",  # Arrived on estimated day -> On-Time
                "2018-06-10 00:00:00",  # Arrived after estimated day -> Delayed
                "2018-07-05 00:00:00",  # Arrived before estimated day -> Early
            ],
        })

        self.order_items_df = pd.DataFrame({
            "order_id": ["o1", "o2", "o3"],
            "order_item_id": [1, 1, 1],
            "price": [100.0, 50.0, 200.0],
            "freight_value": [15.0, 10.0, 25.0],
        })

        self.customers_df = pd.DataFrame({
            "customer_id": ["c1", "c2"],
            "customer_unique_id": ["u1", "u2"],
            "customer_state": ["SP", "RJ"],
        })

        self.reviews_df = pd.DataFrame({
            "order_id": ["o1", "o2", "o3"],
            "review_score": [5, 2, 4],
        })

        self.payments_df = pd.DataFrame({
            "order_id": ["o1", "o1", "o2"],
            "payment_type": ["credit_card", "voucher", "boleto"],
            "payment_value": [80.0, 35.0, 60.0],
        })

    def test_calculate_total_orders(self):
        total = calculate_total_orders(self.orders_df)
        self.assertEqual(total, 3)

    def test_calculate_total_revenue(self):
        gross_rev = calculate_total_revenue(self.order_items_df, include_freight=True)
        net_rev = calculate_total_revenue(self.order_items_df, include_freight=False)
        self.assertEqual(gross_rev, 400.0)
        self.assertEqual(net_rev, 350.0)

    def test_delayed_orders_consistency(self):
        """Ensures calculate_delayed_orders matches delivery_delay_distribution."""
        delayed = calculate_delayed_orders(self.orders_df)
        dist = delivery_delay_distribution(self.orders_df)
        self.assertEqual(delayed, 1)
        self.assertEqual(dist["Delayed"], 1)
        self.assertEqual(dist["On Time"], 1)
        self.assertEqual(dist["Early"], 1)

    def test_calculate_repeat_customer_rate(self):
        repeat_rate = calculate_repeat_customer_rate(self.orders_df, self.customers_df)
        # u1 placed 2 orders (o1, o3), u2 placed 1 order (o2) -> 1/2 = 50%
        self.assertEqual(repeat_rate, 50.0)

    def test_payment_method_analysis_no_double_counting(self):
        payments = payment_method_analysis(self.payments_df)
        total_payment_rev = payments["revenue"].sum()
        self.assertEqual(round(total_payment_rev, 2), 175.0)

    def test_sales_by_state(self):
        states = sales_by_state(self.orders_df, self.customers_df, self.order_items_df)
        self.assertFalse(states.empty)
        self.assertIn("São Paulo", states["state_name"].values)


class DataQualityUnitTests(TestCase):
    """Unit tests for data quality and pipeline integrity."""

    def test_dataset_summary_and_missing_values(self):
        df = pd.DataFrame({
            "col_a": [1, None, 3],
            "col_b": ["x", "y", "z"],
        })
        summary = dataset_summary(df)
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["columns"], 2)

        missing = missing_values_report(df)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["column"], "col_a")
        self.assertEqual(missing[0]["missing_count"], 1)

    def test_data_health_score(self):
        orders = pd.DataFrame({"order_id": ["o1", "o2"], "customer_id": ["c1", "c2"]})
        items = pd.DataFrame({"order_id": ["o1", "o2"]})
        customers = pd.DataFrame({"customer_id": ["c1", "c2"]})
        reviews = pd.DataFrame({"order_id": ["o1", "o2"]})

        health = calculate_data_health_score(orders, items, customers, reviews)
        self.assertGreaterEqual(health["health_score"], 90.0)
        self.assertEqual(health["status"], "Optimal")


class MachineLearningUnitTests(TestCase):
    """Unit tests for the delivery delay ML pipeline and inference."""

    def setUp(self):
        self.orders = pd.DataFrame({
            "order_id": [f"o{i}" for i in range(20)],
            "order_delivered_customer_date": ["2018-05-15 10:00:00"] * 20,
            "order_estimated_delivery_date": ["2018-05-10 00:00:00"] * 10 + ["2018-05-20 00:00:00"] * 10,
        })
        self.items = pd.DataFrame({
            "order_id": [f"o{i}" for i in range(20)],
            "order_item_id": [1] * 20,
            "freight_value": [15.0 + i for i in range(20)],
            "price": [100.0] * 20,
        })

    def test_prepare_delay_dataset(self):
        dataset = prepare_delay_dataset(self.orders, self.items)
        self.assertIn("is_delayed", dataset.columns)
        self.assertFalse(dataset["is_delayed"].isnull().any())

    def test_single_order_inference(self):
        dataset = prepare_delay_dataset(self.orders, self.items)
        train_delay_prediction_model(dataset, force_retrain=True)

        pred = predict_single_order(freight_value=45.0, price=150.0, item_count=2, installments=3)
        self.assertIn("probability_percent", pred)
        self.assertIn("risk_level", pred)
        self.assertGreaterEqual(pred["probability_percent"], 0.0)
        self.assertLessEqual(pred["probability_percent"], 100.0)


class ViewsAndApiIntegrationTests(TestCase):
    """Integration tests for all dashboard views and REST endpoints."""

    def setUp(self):
        self.client = Client()

    def test_dashboard_home_view(self):
        res = self.client.get(reverse("dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Executive Business Overview")

    def test_ml_results_view(self):
        res = self.client.get(reverse("results"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Live Order Delay Risk Simulator")

    def test_data_quality_view(self):
        res = self.client.get(reverse("data_quality"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Data Quality & Pipeline Health Audit")

    def test_upload_data_get(self):
        res = self.client.get(reverse("upload"))
        self.assertEqual(res.status_code, 200)

    def test_upload_data_post_valid_csv(self):
        csv_data = b"order_id,price,status\n101,45.5,delivered\n102,99.0,shipped\n"
        upload_file = SimpleUploadedFile("sample.csv", csv_data, content_type="text/csv")
        res = self.client.post(reverse("upload"), {"file": upload_file})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "File Ingested Successfully!")

    def test_export_kpis_csv(self):
        res = self.client.get(reverse("export_kpis"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv")

    def test_api_kpis_endpoint(self):
        res = self.client.get(reverse("api_kpis"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("orders_count", data)
        self.assertIn("gross_revenue", data)

    def test_api_predict_delay_endpoint(self):
        payload = {
            "freight_value": 30.0,
            "price": 120.0,
            "item_count": 1,
            "installments": 2,
        }
        res = self.client.post(
            reverse("api_predict_delay"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("probability_percent", data)
        self.assertIn("risk_level", data)
