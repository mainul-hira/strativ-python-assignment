import logging

from rest_framework.views import APIView
from rest_framework.response import Response

from travel.services import (
    DistrictMetricsService,
    TravelRecommendationService,
    OpenMeteoError,
)
from travel.api.serializers import TravelRecommendationRequestSerializer
from rest_framework import status


logger = logging.getLogger("general")


class TopDistrictsAPIView(APIView):
    """GET /api/v1/top-districts — return top 10 districts."""

    def get(self, request, *args, **kwargs):
        district_metrics_service = DistrictMetricsService()
        top_10_districts = district_metrics_service.get_top_10_districts()

        return Response(top_10_districts, status=status.HTTP_200_OK)


class TravelRecommendationAPIView(APIView):
    """
    POST /api/v1/travel-recommendation

    Request body:
    {
      "current_lat": 23.8103,
      "current_lon": 90.4125,
      "destination_district_id": 42,
      "travel_date": "2025-12-15"
    }
    """

    def post(self, request, *args, **kwargs):
        serializer = TravelRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        current_lat = data["current_lat"]
        current_lon = data["current_lon"]
        destination = data["destination"]
        travel_date = data["travel_date"]

        service = TravelRecommendationService()

        try:
            result = service.get_recommendation(
                current_lat=current_lat,
                current_lon=current_lon,
                destination=destination,
                travel_date=travel_date,
            )
        except OpenMeteoError as exc:
            return Response(
                {"detail": f"Failed to fetch weather/air-quality data: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception(f"Unexpected error in TravelRecommendationAPIView: {exc}")
            return Response(
                {"detail": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)
