from django.urls import path

from .views import TopDistrictsAPIView

urlpatterns = [
    path("top-districts", TopDistrictsAPIView.as_view(), name="top-districts"),
]
