from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from travel.models import District


class TravelRecommendationRequestSerializer(serializers.Serializer):
    """
    Validates input for the travel recommendation endpoint.

    - current_lat, current_lon: user's current location
    - destination_district_id: PK of District
    - travel_date: date within the next 5 days (Open-Meteo horizon, after 5th day air quality provides null data)
    """

    current_lat = serializers.FloatField()
    current_lon = serializers.FloatField()
    destination_district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source="destination",
    )
    travel_date = serializers.DateField()

    def validate_travel_date(self, value):
        today = timezone.localdate()
        max_date = today + timedelta(days=4)  # 5-day forecast window (today + 4)

        if value < today:
            raise serializers.ValidationError(
                "Travel date must be today or in the future."
            )
        if value > max_date:
            raise serializers.ValidationError(
                f"Travel date must be within the next 5 days (up to {max_date})."
            )
        return value
