from django.urls import path
from .views import dashboard_home, export_kpis, upload_data, Ml_results


urlpatterns = [
    path("", dashboard_home, name="dashboard"),
    path("export-kpis/", export_kpis, name="export_kpis"),
    path("upload_data/", upload_data, name="upload"),
    path("ml_results/", Ml_results, name="results"),
]
