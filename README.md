# 🚀 OmniAnalytics: Production E-Commerce Intelligence & ML Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/Pandas-DataFrames-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-Data%20Viz-FF6384?style=flat&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-10B981?style=flat&logo=pytest&logoColor=white)](#-automated-testing)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://ecommerce-analytics-gcm8.onrender.com/)

> ⚠️ **Notice on Live Demo / Free Tier Hosting:**
> This project is hosted on **Render's Free Tier** at **[https://ecommerce-analytics-gcm8.onrender.com/](https://ecommerce-analytics-gcm8.onrender.com/)**.
> Because it is hosted on a free cloud service, inactive instances automatically go into idle sleep after 15 minutes of inactivity. **The initial page load may take 30 to 50 seconds to spin up the container and load dataset caches into memory.**
> A real-time loading screen with a progress bar and status notifications has been integrated into the app so you can track the server initialization. Once awake, all page navigation and ML predictions are fast and responsive!

An enterprise-grade **Full-Stack E-Commerce Analytics & Machine Learning Platform** built with **Django**, **Pandas**, **Scikit-Learn**, and **Chart.js**. It processes real-world transactional data from the **Olist Brazilian E-Commerce public dataset (100,000+ orders)** to deliver actionable business intelligence, customer cohort analytics, pipeline health audits, and an **interactive real-time ML delay simulator**.

---

## 📑 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quickstart & Local Setup](#-quickstart--local-setup)
- [REST API Reference](#-rest-api-reference)
- [Automated Testing](#-automated-testing)
- [Deployment Guide (Render.com)](#-deployment-guide-rendercom)
- [Resume & Portfolio Highlights](#-resume--portfolio-highlights)

---

## 🧠 Architecture Overview

```
                        ┌───────────────────────────────────────────────┐
                        │      Olist E-Commerce Datasets (9 CSVs)       │
                        │    Orders • Items • Payments • Customers      │
                        └───────────────────────┬───────────────────────┘
                                                │ (Lazy Ingestion)
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │         Dedicated Services Layer              │
                        │  • analytics.py (KPIs, Cohorts, Trends)       │
                        │  • ml_models.py (Pipelines, Standard Scaling) │
                        │  • data_overview.py (Audit & Integrity)       │
                        └───────────────────────┬───────────────────────┘
                                                │ (Sub-50ms)
                                                ▼
                                    ┌───────────────────────┐
                                    │   In-Memory Cache     │
                                    └───────────┬───────────┘
                                                │
                      ┌─────────────────────────┴─────────────────────────┐
                      ▼                                                   ▼
       ┌─────────────────────────────┐                     ┌─────────────────────────────┐
       │   Django MVT Web Views      │                     │     REST API Endpoints      │
       │  • / (Executive Dashboard)  │                     │  • /api/kpis/ (Live JSON)   │
       │  • /ml-results/ (Simulator) │                     │  • /api/predict-delay/      │
       │  • /data-quality/ (Audit)   │                     │  • /export-kpis/ (CSV)      │
       │  • /upload-data/ (Ingestion)│                     └─────────────────────────────┘
       └──────────────┬──────────────┘
                      ▼
       ┌─────────────────────────────────────────────────────────┐
       │  Modern Glassmorphic UI (Bootstrap 5 Dark + Chart.js)   │
       └─────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Features

### 1. Executive Business Intelligence Dashboard (`/`)
* **Core Financial & Volume KPIs**: Unique Orders, Gross Merchandise Value (GMV), Net Product Revenue, SLA Delayed Deliveries, Customer CSAT Rating, and Repeat Buyer Rate.
* **Intelligent Retention Engine**: Heuristic analysis comparing carrier delivery delay rates against second-order conversion rates with executive action recommendations.
* **Visual Analytics Suite**:
  * Multi-year purchase trajectory with interactive year filtering (`2016`, `2017`, `2018`).
  * Top 10 category revenue breakdown with localized currency formatting (`R$`).
  * Fulfillment SLA reliability doughnut chart with center on-time percentage.
  * Average Order Value (AOV) monthly basket size evolution.
  * **Top Merchants Leaderboard**: Highlights top-earning marketplace sellers with geographic location and cumulative gross sales.
  * **Top Regional Markets**: State-by-state breakdown (São Paulo, Rio de Janeiro, Minas Gerais, etc.) with national market share bars.
* **Customer Experience & Payment Diagnostics**:
  * Customer cohort segmentation (New, Returning, Loyal cohorts with respective AOV).
  * CSAT rating drop correlation for delayed deliveries (-1.8 star customer satisfaction penalty).
  * Accurate payment method market share (deduplicating split payments).

### 2. Interactive Machine Learning Delay Simulator (`/ml-results/`)
* **Production Pipeline**: Standardized feature scaling (`StandardScaler`) with class-balanced `LogisticRegression` trained on multi-dimensional features (Freight Cost, Product Price, Item Count, Payment Installments).
* **Statistical Rigor**: Evaluated with Accuracy, Recall, Precision, Harmonized F1, and **ROC-AUC Score**.
* **Confusion Matrix & Feature Weights**: Visual heat-map matrix and standardized coefficients explaining logistic drivers.
* **Live Inference Simulator**: Interactive UI sliders connected to the `/api/predict-delay/` REST endpoint providing real-time probability scores, risk badges (*Low*, *Moderate*, *High Risk*), and dispatch advice.

### 3. Data Quality & Pipeline Integrity Suite (`/data-quality/`)
* **Comprehensive Data Health Score**: Synthesizes duplicate checks, foreign key referential integrity, and null values into an overall health score (e.g. `98.2% Optimal`).
* **Referential Integrity Diagnostics**: Detects orphaned orders and validates 100% foreign key mapping between orders and customers.
* **Missing Value Lifecycle Audit**: Categorizes null values across operational timestamps (purchase, approval, carrier handoff, customer delivery).

### 4. Dataset Ingestion & Schema Inspector (`/upload-data/`)
* **Drag-and-Drop CSV Ingestion**: Functional file upload endpoint with client & server-side validation.
* **Instant Schema & Record Preview**: Inspects uploaded columns, detects duplicate rows, null counts, and displays a formatted 5-row preview table.

---

## 🧱 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Django 5.x (MVT + REST API Endpoints) |
| **Data Processing & ETL** | Pandas, NumPy (Vectorized operations & aggregations) |
| **Machine Learning** | Scikit-Learn (`Pipeline`, `StandardScaler`, `LogisticRegression`) |
| **Frontend UI** | HTML5, Modern Vanilla CSS3 (Glassmorphism, CSS Variables, Tokens) |
| **Data Visualization** | Chart.js (Responsive line, bar, doughnut charts with custom plugins) |
| **Typography** | Google Fonts (`Outfit` & `Plus Jakarta Sans`) |
| **Testing** | Django Test Framework (18 Automated Unit & Integration Tests) |
| **WSGI Server** | Gunicorn (Production web server) |

---

## 📁 Project Structure

```
ecommerce_analytics/
├── dashboard/
│   ├── services/
│   │   ├── analytics.py        # Business KPIs, time trends, regional state sales
│   │   ├── default_dataset.py  # Lazy dataset loader with in-memory caching
│   │   ├── data_overview.py    # Data quality, health score, and foreign key audits
│   │   └── ml_models.py        # Scikit-Learn delay prediction pipeline & simulator
│   ├── static/
│   │   ├── css/                # Glassmorphic dark styling (dashboard, results, upload)
│   │   └── js/charts.js        # Chart.js rendering & live ML simulator API client
│   ├── templates/dashboard/
│   │   ├── base.html           # Master layout with responsive sidebar & status chips
│   │   └── pages/              # dashboard.html, results.html, data_quality.html, upload.html
│   ├── tests.py                # 18 automated unit and integration tests
│   ├── urls.py                 # Route definitions & REST API URLs
│   └── views.py                # View controllers with sub-50ms caching
├── data/default/               # Olist Brazilian E-Commerce CSV dataset files
├── ecommerce_analytics/        # Django project root settings, wsgi, and urls
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Enter Repository
```bash
git clone https://github.com/Sriram-Harshit/ecommerce_analytics.git
cd ecommerce_analytics
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations & Start Server
```bash
python manage.py migrate
python manage.py runserver
```

### 5. Access the Platform
Open your browser at: **`http://127.0.0.1:8000/`**
- **Executive Dashboard**: `http://127.0.0.1:8000/`
- **ML Risk Simulator**: `http://127.0.0.1:8000/ml-results/`
- **Data Quality Audit**: `http://127.0.0.1:8000/data-quality/`
- **Dataset Ingestion**: `http://127.0.0.1:8000/upload-data/`
- **REST KPI Endpoint**: `http://127.0.0.1:8000/api/kpis/`

---

## 📈 REST API Reference

### 1. Delivery Delay Prediction API
* **Endpoint**: `POST /api/predict-delay/`
* **Content-Type**: `application/json`

**Sample Request**:
```json
{
  "freight_value": 35.50,
  "price": 180.00,
  "item_count": 2,
  "installments": 3
}
```

**Sample Response**:
```json
{
  "probability_percent": 68.4,
  "risk_level": "High Risk",
  "badge_class": "danger",
  "recommendation": "High delay probability! Recommend expedited carrier routing or priority dispatch.",
  "inputs": {
    "freight_value": 35.5,
    "price": 180.0,
    "item_count": 2,
    "installments": 3
  }
}
```

### 2. Core Business KPIs API
* **Endpoint**: `GET /api/kpis/`

**Sample Response**:
```json
{
  "orders_count": 99441,
  "gross_revenue": 15843527.19,
  "product_revenue": 13591643.7,
  "delayed_orders": 6535,
  "avg_review": 4.09,
  "repeat_rate": 3.12,
  "health_score": 98.2
}
```

---

## 🧪 Automated Testing

The project includes an **18-test automated test suite** in [dashboard/tests.py](dashboard/tests.py) testing data aggregations, data quality audits, ML inference bounds, and REST endpoint HTTP responses.

Run the test suite:
```bash
python manage.py test
```

**Expected Output**:
```text
Creating test database for alias 'default'...
..................
----------------------------------------------------------------------
Ran 18 tests in ~6.9s

OK
Destroying test database for alias 'default'...
System check identified no issues (0 silenced).
```

---

## 🌐 Deployment & Live Hosting (Render.com)

* **Live Platform URL**: [https://ecommerce-analytics-gcm8.onrender.com/](https://ecommerce-analytics-gcm8.onrender.com/)
* **Hosting Tier**: Render Free Web Service
* **Cold-Start Performance Note**: Render spins down free containers after 15 minutes of inactivity. If visiting after an idle period, **the first request takes ~30–50 seconds to spin up the container and load the dataset into RAM**. The application includes an in-app loading overlay and progress bar that provides real-time feedback while the instance starts up. Once warmed, all subsequent dashboard views and API queries are near-instant (<100ms).

### Deploying Your Own Instance:
1. Push your repository to **GitHub**.
2. Go to [dashboard.render.com](https://dashboard.render.com/) and click **"New +"** → **"Web Service"** (or use the included [render.yaml](render.yaml) blueprint).
3. Select your repository `ecommerce_analytics`.
4. Configure the settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate`
   - **Start Command**: `gunicorn ecommerce_analytics.wsgi:application --workers 1 --threads 4 --timeout 120`
5. Click **"Create Web Service"** to launch your live platform with a free HTTPS URL.

---

## 🎯 Resume & Portfolio Highlights
- **Full-Stack Django Architecture**: Engineered an enterprise analytics platform processing 100k+ transactional records with sub-50ms response times via lazy ingestion and in-memory caching.
- **Production Data Engineering**: Handled 100,000+ transactional records across 9 relational tables; resolved critical double-counting and KPI discrepancies.
- **Applied Machine Learning**: Engineered real-time ML pipelines handling class imbalance, feature normalization, and interactive client-side inference.
- **Geographic Demand Breakdown**: Developed regional market analytics classifying sales volume across top Brazilian states.
- **Rigorous Software Quality**: Implemented a comprehensive 18-test automated test suite ensuring high reliability across all data transformations and API contracts.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
