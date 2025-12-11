from rest_framework.views import APIView
from rest_framework.response import Response

from travel.services import DistrictMetricsService


class TopDistrictsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        district_metrics_service = DistrictMetricsService()
        top_10_districts = district_metrics_service.get_top_10_districts()

        return Response(top_10_districts)
