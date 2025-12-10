from django.db import models


class District(models.Model):
    """
    Populated from bd-districts.json via a management command.
    """

    name = models.CharField(max_length=100, unique=True)
    name_bn = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()
    division_id = models.PositiveIntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DistrictMetrics(models.Model):
    """
    Latest 7-day aggregated metrics.

    - avg_temp_2pm_7day: average of daily temperature at 14:00 for next 7 days
    - avg_pm25_7day: average PM2.5 (we'll also use 14:00 daily, averaged)
    """

    district = models.OneToOneField(
        District,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    avg_temp_2pm_7day = models.FloatField()
    avg_pm25_7day = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Metrics({self.district.name})"
