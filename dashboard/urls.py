from django.urls import path
from .views import (
    dashboard_home,
    export_kpis,
    upload_data,
    ml_results,
    data_quality_view,
    api_kpis,
    api_predict_delay,
)

urlpatterns = [
    # Pages
    path("", dashboard_home, name="dashboard"),
    path("ml-results/", ml_results, name="results"),
    path("ml_results/", ml_results, name="results_legacy"),
    path("data-quality/", data_quality_view, name="data_quality"),
    path("upload-data/", upload_data, name="upload"),
    path("upload_data/", upload_data, name="upload_legacy"),
    path("export-kpis/", export_kpis, name="export_kpis"),
    
    # REST API Endpoints
    path("api/kpis/", api_kpis, name="api_kpis"),
    path("api/predict-delay/", api_predict_delay, name="api_predict_delay"),
]
