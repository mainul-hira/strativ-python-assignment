from django.core.management.base import BaseCommand
from travel.services import DistrictMetricsService


class Command(BaseCommand):
    help = "Update 7-day average 2PM temperature and PM2.5 for all districts."

    def handle(self, *args, **options):
        self.stdout.write("Updating district metrics...")

        service = DistrictMetricsService()
        created_count, updated_count = service.refresh_all_metrics()

        if updated_count == 0 and created_count == 0:
            self.stdout.write(
                self.style.WARNING("No district metrics were updated or created.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated metrics for {updated_count} districts and created metrics for {created_count} districts."
                )
            )
