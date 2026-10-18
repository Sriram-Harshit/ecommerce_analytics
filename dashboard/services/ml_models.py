import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

# Global in-memory cache for the trained pipeline & evaluation metrics
_TRAINED_MODEL_CACHE: Dict[str, Any] = {}


def prepare_delay_dataset(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    payments_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Constructs an engineered feature dataset for delivery delay classification.
    Features:
    - freight_value: Total shipping freight cost
    - price: Total merchandise purchase price
    - item_count: Total quantity of items in the order
    - payment_installments: Installments selected by customer
    """
    # 1. Aggregate item features per order
    item_agg = order_items_df.groupby("order_id", as_index=False).agg(
        freight_value=("freight_value", "sum"),
        price=("price", "sum"),
        item_count=("order_item_id", "count"),
    )

    # 2. Merge with orders
    df = orders_df.merge(item_agg, on="order_id", how="inner")

    # 3. Optional payment installment feature
    if payments_df is not None:
        pay_agg = payments_df.groupby("order_id", as_index=False).agg(
            payment_installments=("payment_installments", "max")
        )
        df = df.merge(pay_agg, on="order_id", how="left")
        df["payment_installments"] = df["payment_installments"].fillna(1)
    else:
        df["payment_installments"] = 1

    # 4. Convert timestamps safely with coercion BEFORE filtering
    df["delivered"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
    df["estimated"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")

    # 5. Drop invalid or unfulfilled orders
    df = df.dropna(subset=["delivered", "estimated"]).copy()

    # 6. Binary ground truth: 1 if delivered past estimated calendar date, else 0
    df["is_delayed"] = (df["delivered"].dt.date > df["estimated"].dt.date).astype(int)

    return df


def train_delay_prediction_model(df: pd.DataFrame, force_retrain: bool = False) -> Dict[str, Any]:
    """
    Trains a normalized Logistic Regression classifier with class balancing.
    Caches the trained model so subsequent page loads are instantaneous.
    """
    global _TRAINED_MODEL_CACHE
    if not force_retrain and "metrics" in _TRAINED_MODEL_CACHE:
        return _TRAINED_MODEL_CACHE["metrics"]

    features = ["freight_value", "price", "item_count", "payment_installments"]
    X = df[features].fillna(0)
    y = df["is_delayed"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Production ML Pipeline with Feature Scaling
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(class_weight="balanced", random_state=42, max_iter=500)),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    acc = round(accuracy_score(y_test, y_pred), 3)
    prec = round(precision_score(y_test, y_pred, zero_division=0), 3)
    rec = round(recall_score(y_test, y_pred, zero_division=0), 3)
    f1 = round(f1_score(y_test, y_pred, zero_division=0), 3)
    auc = round(roc_auc_score(y_test, y_proba), 3)

    cm = confusion_matrix(y_test, y_pred)
    conf_matrix = {
        "tn": int(cm[0][0]),
        "fp": int(cm[0][1]),
        "fn": int(cm[1][0]),
        "tp": int(cm[1][1]),
    }

    # Normalized feature coefficients
    coefs = pipeline.named_steps["classifier"].coef_[0]
    feature_importance = {
        feat: round(float(coef), 3) for feat, coef in zip(features, coefs)
    }

    metrics = {
        "model_name": "Logistic Regression (Standardized + Balanced)",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": auc,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "confusion_matrix": conf_matrix,
        "feature_importance": feature_importance,
    }

    _TRAINED_MODEL_CACHE["pipeline"] = pipeline
    _TRAINED_MODEL_CACHE["features"] = features
    _TRAINED_MODEL_CACHE["metrics"] = metrics

    return metrics


def predict_single_order(
    freight_value: float,
    price: float,
    item_count: int = 1,
    installments: int = 1,
) -> Dict[str, Any]:
    """
    Performs real-time delay probability inference for an arbitrary order.
    Used for interactive ML simulations in the dashboard.
    """
    global _TRAINED_MODEL_CACHE
    pipeline = _TRAINED_MODEL_CACHE.get("pipeline")

    if pipeline is None:
        return {
            "error": "Model not trained yet",
            "probability": 0.0,
            "risk_level": "Unknown",
        }

    input_df = pd.DataFrame([{
        "freight_value": float(freight_value),
        "price": float(price),
        "item_count": int(item_count),
        "payment_installments": int(installments),
    }])

    proba = float(pipeline.predict_proba(input_df)[0][1])
    pct = round(proba * 100, 1)

    if pct >= 60.0:
        risk_level = "High Risk"
        badge_class = "danger"
        recommendation = "High delay probability! Recommend expedited carrier routing or priority dispatch."
    elif pct >= 35.0:
        risk_level = "Moderate Risk"
        badge_class = "warning"
        recommendation = "Moderate shipping friction. Monitor warehouse handoff and notify customer of realistic timeline."
    else:
        risk_level = "Low Risk"
        badge_class = "success"
        recommendation = "Optimal shipping profile. Standard logistics transit should meet promised delivery SLA."

    return {
        "probability_percent": pct,
        "risk_level": risk_level,
        "badge_class": badge_class,
        "recommendation": recommendation,
        "inputs": {
            "freight_value": freight_value,
            "price": price,
            "item_count": item_count,
            "installments": installments,
        },
    }
