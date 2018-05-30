from django.core.management.base import BaseCommand
from trainer.models import User, Solution
import tablib


class Command(BaseCommand):

    help = 'Export all solutions to excel file.'

    def handle(self, *args, **options):

        data = tablib.Dataset()
        data.headers = ['user_id',          # User.id
                        'user_level',             # Maximaler Level
                        ]

        count = 0

        for u in User.objects.all():
            if u.solution_set.count() == 0:
                continue
            row = []
            row.append(u.id)
            row.append(u.rules_activated_count)
            data.append(row)
            count += 1
            if count % 100 == 0:
                self.stdout.write('{} Zeilen erstellt'.format(count))

        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_userlevels.csv', 'wb') as f:
            f.write(data.csv)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} users.'.format(count)))
