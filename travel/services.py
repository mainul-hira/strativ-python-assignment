import logging
import requests
from statistics import fmean
from typing import Any

from django.db import transaction
from django.utils import timezone

from travel.models import District, DistrictMetrics

logger = logging.getLogger("general")


class OpenMeteoError(Exception):
    """Base exception for Open-Meteo related errors."""


class OpenMeteoClient:
    """
    Provides only 4 API calls:
      - 7-day weather forecast (hourly)
      - 7-day air quality (hourly)
      - Single-day weather (hourly)
      - Single-day air quality (hourly)
    """

    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, url: str, params: dict):
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            logger.error(f"OpenMeteo request failed: {e}")
            raise OpenMeteoError(f"Request failed: {e}")

        if resp.status_code != 200:
            raise OpenMeteoError(
                f"OpenMeteo error {resp.status_code}: {resp.text[:200]}"
            )

        try:
            return resp.json()
        except ValueError:
            raise OpenMeteoError("Invalid JSON response from Open-Meteo")

    @staticmethod
    def _build_multi_coordinate_params(
        coords: list[tuple[float, float]],
    ) -> dict[str, str]:
        """
        Build latitude/longitude params for multiple coordinates.

        Open-Meteo accepts comma separated values, e.g:
        latitude=23.7115253,23.6070822&longitude=90.4111451,89.8429406
        """
        if not coords:
            raise ValueError("coords must not be empty")

        latitudes = ",".join(f"{c[0]}" for c in coords)
        longitudes = ",".join(f"{c[1]}" for c in coords)

        return {"latitude": latitudes, "longitude": longitudes}

    def get_multi_weather_7d(self, coords: list[tuple[float, float]]) -> dict[str, Any]:
        """
        Fetch 7-day hourly weather (temperature_2m) for multiple coordinates.
        """
        params = self._build_multi_coordinate_params(coords)
        params.update(
            {
                "hourly": "temperature_2m",
                "forecast_days": 7,
                "timezone": "Asia/Dhaka",
            }
        )

        return self._get(self.WEATHER_URL, params)

    def get_multi_air_quality_7d(
        self,
        coords: list[tuple[float, float]],
    ) -> dict[str, Any]:
        """
        Fetch 7-day hourly air quality (pm2_5) for multiple coordinates.
        """
        params = self._build_multi_coordinate_params(coords)
        params.update(
            {
                "hourly": "pm2_5",
                "forecast_days": 7,
                "timezone": "Asia/Dhaka",
            }
        )

        return self._get(self.AIR_QUALITY_URL, params)

    def get_weather_single_day(self, lat: float, lon: float, date: str):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m",
            "start_date": date,
            "end_date": date,
            "timezone": "Asia/Dhaka",
        }
        return self._get(self.WEATHER_URL, params)

    def get_air_quality_single_day(self, lat: float, lon: float, date: str):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm2_5",
            "start_date": date,
            "end_date": date,
            "timezone": "Asia/Dhaka",
        }
        return self._get(self.AIR_QUALITY_URL, params)


class DistrictMetricsService:
    """
    Service responsible for:
    - Fetching 7-day weather and air quality for all districts from Open-Meteo
    - Computing:
        * average temperature at 14:00 (2 PM) over 7 days
        * average PM2.5 at 14:00 over 7 days
    - Upserting rows into DistrictMetrics
    """

    def __init__(self, client: OpenMeteoClient | None = None) -> None:
        self.client = client or OpenMeteoClient()

    @staticmethod
    def _compute_avg_2pm(
        hourly: dict[str, list[str | float | None]], value_key: str
    ) -> float | None:
        """
        Given the 'hourly' section of the response and a value key
        (e.g. 'temperature_2m' or 'pm2_5'), extract values at 14:00
        for each day and return their mean over the 7-day period.

        timezone=Asia/Dhaka so 'T14:00' means 2 PM local.
        """
        times: list[str] = hourly.get("time", [])
        values: list[float] = hourly.get(value_key, [])

        if not times or not values or len(times) != len(values):
            return None

        two_pm_values: list[float] = []

        for time, value in zip(times, values):
            # we expect some air quality data to be null from Open-Meteo
            if isinstance(time, str) and time.endswith("T14:00") and value is not None:
                try:
                    two_pm_values.append(float(value))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {time}: {value}")

        return round(fmean(two_pm_values), 3) if two_pm_values else None

    def refresh_all_metrics(self) -> tuple[int, int]:
        """
        Fetch data for all districts and update DistrictMetrics table.
        """

        districts = list(District.objects.all())

        created_count, updated_count = 0, 0

        if not districts:
            logger.warning(
                "No districts found in database. load districts with python manage.py load_districts"
            )
            return created_count, updated_count

        coordinates: list[tuple[float, float]] = [
            (district.latitude, district.longitude) for district in districts
        ]

        try:
            weather_locations = self.client.get_multi_weather_7d(coords=coordinates)
            air_locations = self.client.get_multi_air_quality_7d(coords=coordinates)
        except OpenMeteoError as exc:
            logger.error(f"Failed to fetch data from Open-Meteo: {exc}")
            raise OpenMeteoError("Failed to fetch data from Open-Meteo")

        if len(weather_locations) != len(districts) or len(air_locations) != len(
            districts
        ):
            logger.error(
                f"Mismatch between number of districts and Open-Meteo locations: "
                f"districts={len(districts)}, weather_locations={len(weather_locations)}, air_locations={len(air_locations)}"
            )
            raise OpenMeteoError(
                "Location count mismatch between districts and Open-Meteo response"
            )

        with transaction.atomic():
            now = timezone.now()

            for district, weather_loc, air_loc in zip(
                districts, weather_locations, air_locations
            ):
                hourly_weather = weather_loc.get("hourly", {})
                hourly_air = air_loc.get("hourly", {})

                avg_temp = self._compute_avg_2pm(
                    hourly_weather, value_key="temperature_2m"
                )
                avg_pm25 = self._compute_avg_2pm(hourly_air, value_key="pm2_5")
                # logger.info(
                #     f"Computed metrics for district {district.name}: avg_temp={avg_temp}, avg_pm25={avg_pm25}"
                # )

                if avg_temp is None or avg_pm25 is None:
                    logger.warning(
                        f"Skipping metrics for district {district.name} due to missing data (avg_temp={avg_temp}, avg_pm25={avg_pm25})"
                    )
                    continue

                metrics_obj, created = DistrictMetrics.objects.update_or_create(
                    district=district,
                    defaults={
                        "avg_temp_2pm_7day": avg_temp,
                        "avg_pm25_7day": avg_pm25,
                        "last_updated": now,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        logger.info(
            f"Refreshed metrics for {len(districts)} districts: created {created_count}, updated {updated_count}"
        )
        return created_count, updated_count
