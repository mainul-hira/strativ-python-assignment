from django.urls import path

from .views import TopDistrictsAPIView, TravelRecommendationAPIView, DistrictAPIView

urlpatterns = [
    path("top-districts", TopDistrictsAPIView.as_view(), name="top-districts"),
    path(
        "travel-recommendation",
        TravelRecommendationAPIView.as_view(),
        name="travel-recommendation",
    ),
    path("districts", DistrictAPIView.as_view(), name="districts"),
]
