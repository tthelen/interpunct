from django.core.management.base import BaseCommand
from trainer.models import User, Solution
import tablib


class Command(BaseCommand):

    help = 'Export some data for correlation calculations to excel file.'

    def handle(self, *args, **options):

        data = tablib.Dataset()
        data.headers = ['user_id',          # User.id
                        'level',
                        'tries',
                        'total_errors/level',
                        'set_errors/level',
                        'correct_errors/level',
                        'explain_errors/level',
                        'germanistik (yes=1/no=0)',
                        'master (1/0)',
                        'self_estimation',
                        'orthosem'
                        ]

        count = 0

        for u in User.objects.all():
            if u.solution_set.count() == 0:
                continue
            row = []
            row.append(u.id)
            level = u.rules_activated_count
            if level == 0:
                level = 0.000000001
            row.append(level)
            row.append(u.tries())
            row.append(u.errors()/level)
            row.append(u.errors(type='set') / level)
            row.append(u.errors(type='correct') / level)
            row.append(u.errors(type='explain') / level)
            germanistik = u.explicit_data_subject1().find('Germanistik') + 1 +\
                          u.explicit_data_subject2().find('Germanistik') + 1 + \
                          u.explicit_data_subject3().find('Germanistik') + 1
            germanistik = 1 if germanistik > 0 else 0
            row.append(germanistik)
            master = 1 if u.explicit_data_study().find('Master') > -1 else 0
            row.append(master)
            row.append(u.data_selfestimation)
            row.append(1 if u.data_orthosem_participant else 0)

            data.append(row)
            count += 1
            if count % 100 == 0:
                self.stdout.write('{} Zeilen erstellt'.format(count))


        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_correlation_data.xlsx', 'wb') as f:
            f.write(data.xlsx)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} users.'.format(count)))
