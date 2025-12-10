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
