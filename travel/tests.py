from datetime import date, timedelta

from django.test import TestCase

from travel.models import District, DistrictMetrics
from travel.services import (
    DistrictMetricsService,
    TravelRecommendationService,
    OpenMeteoError,
)


class FakeOpenMeteoClient:
    """Minimal fake client for testing."""

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def get_multi_weather_7d(self, coords):
        if self.should_fail:
            raise OpenMeteoError("Test error")

        # Return valid weather data for each coordinate
        results = []
        today = date.today()
        for _ in coords:
            times = [
                (today + timedelta(days=i)).isoformat() + "T14:00" for i in range(7)
            ]
            temps = [25.0, 26.0, 24.5, 25.5, 26.5, 25.0, 24.0]
            results.append({"hourly": {"time": times, "temperature_2m": temps}})
        return results

    def get_multi_air_quality_7d(self, coords):
        if self.should_fail:
            raise OpenMeteoError("Test error")

        # Return valid air quality data for each coordinate
        results = []
        today = date.today()
        for _ in coords:
            times = [
                (today + timedelta(days=i)).isoformat() + "T14:00" for i in range(7)
            ]
            pm_values = [40.0, 38.0, 42.0, 39.0, 37.0, 41.0, 40.0]
            results.append({"hourly": {"time": times, "pm2_5": pm_values}})
        return results


class DistrictMetricsServiceTests(TestCase):
    def setUp(self):
        self.district = District.objects.create(
            name="Test District", latitude=23.5, longitude=90.0, division_id=1
        )

    def test_refresh_all_metrics_creates_metrics(self):
        """Test that metrics are created for districts."""
        service = DistrictMetricsService(client=FakeOpenMeteoClient())
        created_count, updated_count = service.refresh_all_metrics()

        self.assertEqual(created_count, 1)
        self.assertEqual(updated_count, 0)
        self.assertTrue(DistrictMetrics.objects.filter(district=self.district).exists())

    def test_refresh_all_metrics_updates_existing_metrics(self):
        """Test that running refresh again updates existing metrics."""
        service = DistrictMetricsService(client=FakeOpenMeteoClient())

        # First run - creates metrics
        created_count, updated_count = service.refresh_all_metrics()
        self.assertEqual(created_count, 1)
        self.assertEqual(updated_count, 0)

        # Second run - updates metrics
        created_count, updated_count = service.refresh_all_metrics()
        self.assertEqual(created_count, 0)
        self.assertEqual(updated_count, 1)

    def test_refresh_all_metrics_handles_errors(self):
        """Test that API errors are raised properly."""
        service = DistrictMetricsService(client=FakeOpenMeteoClient(should_fail=True))

        with self.assertRaises(OpenMeteoError):
            service.refresh_all_metrics()

    def test_get_top_10_districts(self):
        """Test that top 10 districts are returned correctly."""
        for i in range(15):
            district = District.objects.create(
                name=f"District {i}",
                latitude=23.0 + i * 0.1,
                longitude=90.0 + i * 0.1,
                division_id=1,
            )
            DistrictMetrics.objects.create(
                district=district,
                avg_temp_2pm_7day=25.0 + i,
                avg_pm25_7day=40.0 + i,
            )

        service = DistrictMetricsService(client=FakeOpenMeteoClient())
        top_districts = service.get_top_10_districts()

        # Should return exactly 10 districts
        self.assertEqual(len(top_districts), 10)

        # First district should have lowest temperature
        self.assertEqual(top_districts[0]["district_name"], "District 0")
        self.assertEqual(top_districts[0]["rank"], 1)

        # Last should be District 9
        self.assertEqual(top_districts[9]["district_name"], "District 9")
        self.assertEqual(top_districts[9]["rank"], 10)

    def test_refresh_with_no_districts(self):
        """Test that refresh handles empty database gracefully."""
        District.objects.all().delete()
        service = DistrictMetricsService(client=FakeOpenMeteoClient())

        created_count, updated_count = service.refresh_all_metrics()

        self.assertEqual(created_count, 0)
        self.assertEqual(updated_count, 0)


class FakeTravelClient:
    """Fake client for travel recommendation testing."""

    def __init__(
        self, current_temp=30.0, current_pm=50.0, dest_temp=25.0, dest_pm=30.0
    ):
        self.current_temp = current_temp
        self.current_pm = current_pm
        self.dest_temp = dest_temp
        self.dest_pm = dest_pm

    def get_weather_single_day(self, lat, lon, travel_date):
        """Returns weather data for current location and destination."""
        return [
            {"hourly": {"temperature_2m": [self.current_temp]}},
            {"hourly": {"temperature_2m": [self.dest_temp]}},
        ]

    def get_air_quality_single_day(self, lat, lon, travel_date):
        """Returns air quality data for current location and destination."""
        return [
            {"hourly": {"pm2_5": [self.current_pm]}},
            {"hourly": {"pm2_5": [self.dest_pm]}},
        ]


class TravelRecommendationServiceTests(TestCase):
    def setUp(self):
        self.destination = District.objects.create(
            name="Sylhet", latitude=24.8949, longitude=91.8687, division_id=1
        )
        self.travel_date = date.today() + timedelta(days=2)

    def test_recommendation_cooler_and_cleaner(self):
        """Test recommendation when destination is cooler and has better air quality."""
        client = FakeTravelClient()
        service = TravelRecommendationService(client=client)

        result = service.get_recommendation(
            current_lat=23.8103,
            current_lon=90.4125,
            destination=self.destination,
            travel_date=self.travel_date,
        )

        self.assertEqual(result["status"], "Recommended")
        self.assertIn("cooler", result["reason"])
        self.assertIn("better air quality", result["reason"])
        self.assertEqual(result["current"]["temperature_2pm"], 30.0)
        self.assertEqual(result["destination"]["temperature_2pm"], 25.0)

    def test_recommendation_hotter_and_worse_air(self):
        """Test recommendation when destination is hotter and has worse air quality."""
        # Current: 25°C, 30 PM2.5 | Destination: 32°C, 60 PM2.5
        client = FakeTravelClient(
            current_temp=25.0, current_pm=30.0, dest_temp=32.0, dest_pm=60.0
        )
        service = TravelRecommendationService(client=client)

        result = service.get_recommendation(
            current_lat=23.8103,
            current_lon=90.4125,
            destination=self.destination,
            travel_date=self.travel_date,
        )

        self.assertEqual(result["status"], "Not Recommended")
        self.assertIn("hotter", result["reason"])
        self.assertIn("worse air quality", result["reason"])

    def test_recommendation_hotter_only(self):
        """Test recommendation when destination is hotter but air quality is same/better."""
        # Current: 25°C, 50 PM2.5 | Destination: 30°C, 40 PM2.5
        client = FakeTravelClient(
            current_temp=25.0, current_pm=50.0, dest_temp=30.0, dest_pm=40.0
        )
        service = TravelRecommendationService(client=client)

        result = service.get_recommendation(
            current_lat=23.8103,
            current_lon=90.4125,
            destination=self.destination,
            travel_date=self.travel_date,
        )

        self.assertEqual(result["status"], "Not Recommended")
        self.assertIn("hotter", result["reason"])

    def test_recommendation_includes_all_data(self):
        """Test that recommendation includes all required data fields."""
        client = FakeTravelClient()
        service = TravelRecommendationService(client=client)

        result = service.get_recommendation(
            current_lat=23.8103,
            current_lon=90.4125,
            destination=self.destination,
            travel_date=self.travel_date,
        )

        # Check all required fields are present
        self.assertIn("status", result)
        self.assertIn("reason", result)
        self.assertIn("travel_date", result)
        self.assertIn("current", result)
        self.assertIn("destination", result)
        self.assertIn("temperature_2pm", result["current"])
        self.assertIn("pm25_2pm", result["current"])
        self.assertIn("district", result["destination"])
        self.assertEqual(result["destination"]["district"], "Sylhet")

    def test_recommendation_with_missing_data(self):
        """Test that missing data (None values) raises OpenMeteoError."""

        class FakeClientWithMissingData:
            """Client that returns None for temperature."""

            def get_weather_single_day(self, lat, lon, travel_date):
                return [
                    {"hourly": {"temperature_2m": [None]}},  # Missing current temp
                    {"hourly": {"temperature_2m": [25.0]}},
                ]

            def get_air_quality_single_day(self, lat, lon, travel_date):
                return [
                    {"hourly": {"pm2_5": [50.0]}},
                    {"hourly": {"pm2_5": [30.0]}},
                ]

        service = TravelRecommendationService(client=FakeClientWithMissingData())

        with self.assertRaises(OpenMeteoError) as context:
            service.get_recommendation(
                current_lat=23.8103,
                current_lon=90.4125,
                destination=self.destination,
                travel_date=self.travel_date,
            )

        self.assertIn("Missing 2 PM data", str(context.exception))
