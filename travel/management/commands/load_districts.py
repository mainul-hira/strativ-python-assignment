import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from travel.models import District


class Command(BaseCommand):
    help = "Load district data into the District table from JSON."

    def handle(self, *args, **options):
        file_path = f"{settings.BASE_DIR}/data/bd-districts.json"
        self.stdout.write(f"Loading district data from file:\n  {file_path}")

        if not os.path.exists(file_path):
            raise CommandError(f"File does not exist: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Failed to parse JSON file {file_path}: {exc}") from exc

        districts_data = raw_data.get("districts")
        if not isinstance(districts_data, list):
            raise CommandError("Expected 'districts' key with a list in JSON.")

        created_count = 0
        updated_count = 0
        district_obj_list = []
        district_count = District.objects.count()

        for item in districts_data:
            name = item.get("name")
            name_bn = item.get("bn_name")
            lat = item.get("lat")
            lon = item.get("long")
            division_id = item.get("division_id")

            if not all([name, name_bn, lat, lon, division_id]):
                self.stdout.write(self.style.WARNING(f"Skipping invalid item: {item}"))
                continue

            try:
                lat_f = float(lat)
                lon_f = float(lon)
                div_id = int(division_id)
            except (TypeError, ValueError):
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping invalid data for {name!r}: lat={lat}, long={lon}, div={division_id}"
                    )
                )
                continue

            # for the first time load all the data into the list
            if district_count == 0:
                district_obj_list.append(
                    District(
                        name=name,
                        name_bn=name_bn,
                        latitude=lat_f,
                        longitude=lon_f,
                        division_id=div_id,
                    )
                )
            else:
                obj, created = District.objects.update_or_create(
                    name=name,
                    defaults={
                        "name_bn": name_bn,
                        "latitude": lat_f,
                        "longitude": lon_f,
                        "division_id": div_id,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        if district_obj_list:
            District.objects.bulk_create(district_obj_list)
            self.stdout.write(
                self.style.SUCCESS(
                    f"District load complete. Created={len(district_obj_list)}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"District load complete. Created={created_count}, Updated={updated_count}"
                )
            )
