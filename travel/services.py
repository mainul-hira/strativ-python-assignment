import logging
import requests

logger = logging.getLogger("general")


class OpenMeteoError(Exception):
    """Base exception for Open-Meteo related errors."""


class OpenMeteoClientSimple:
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
            logger.error("OpenMeteo request failed: %s", e)
            raise OpenMeteoError(f"Request failed: {e}")

        if resp.status_code != 200:
            raise OpenMeteoError(
                f"OpenMeteo error {resp.status_code}: {resp.text[:200]}"
            )

        try:
            return resp.json()
        except ValueError:
            raise OpenMeteoError("Invalid JSON response from Open-Meteo")

    def get_multi_weather_7d(self):
        pass

    def get_multi_air_quality_7d(self):
        pass

    def get_weather_single_day(
        self, lat: float, lon: float, date: str, timezone: str = "Asia/Dhaka"
    ):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m",
            "start_date": date,
            "end_date": date,
            "timezone": timezone,
        }
        return self._get(self.WEATHER_URL, params)

    def get_air_quality_single_day(
        self, lat: float, lon: float, date: str, timezone: str = "Asia/Dhaka"
    ):
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm2_5",
            "start_date": date,
            "end_date": date,
            "timezone": timezone,
        }
        return self._get(self.AIR_QUALITY_URL, params)
