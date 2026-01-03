import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
)


def prepare_delay_dataset(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    WHAT:
    Prepare dataset for delivery delay prediction

    WHY:
    Delivery dates come from orders
    Freight value comes from order_items
    """

    # Aggregate freight value per order
    freight_per_order = (
        order_items_df.groupby("order_id")["freight_value"].sum().reset_index()
    )

    # Merge with orders
    df = orders_df.merge(
        freight_per_order,
        on="order_id",
        how="inner",
    )

    # Drop rows with missing dates
    df = df.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    # Convert to datetime safely
    df["order_delivered_customer_date"] = pd.to_datetime(
        df["order_delivered_customer_date"], errors="coerce"
    )
    df["order_estimated_delivery_date"] = pd.to_datetime(
        df["order_estimated_delivery_date"], errors="coerce"
    )

    # Target variable
    df["is_delayed"] = (
        df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    ).astype(int)

    return df


def train_delay_prediction_model(df: pd.DataFrame) -> dict:
    """
    Train a simple, explainable logistic regression model
    to predict delivery delays.
    """

    # Using a single interpretable feature to keep the model explainable
    X = df[["freight_value"]].fillna(0)
    y = df["is_delayed"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression(class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)

    cm = confusion_matrix(y_test, y_pred)

    conf_matrix = {
        "tn": int(cm[0][0]),
        "fp": int(cm[0][1]),
        "fn": int(cm[1][0]),
        "tp": int(cm[1][1]),
    }

    return {
        "model_name": "Logistic Regression",
        "accuracy": round(accuracy, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "confusion_matrix": conf_matrix,
        "feature_importance": {"freight_value": round(float(model.coef_[0][0]), 3)},
    }
