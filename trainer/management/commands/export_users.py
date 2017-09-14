from django.core.management.base import BaseCommand
from trainer.models import User, Solution
import tablib


class Command(BaseCommand):

    help = 'Export all solutions to excel file.'

    def handle(self, *args, **options):

        data = tablib.Dataset()
        data.headers = ['user_id',          # User.id
                        'user_study',       # Studienabschluss
                        'user_semester',    # Semester
                        'user_subject1',    # Erstes Fach
                        'user_subject2',    # Zweites Fach
                        'user_subject3',    #  Drittes Fach
                        'user_study_permission',  # HZB
                        'user_self_estimation',   # selbsteinschätzung
                        'user_sex',               # Geschlecht
                        'user_language',          # Muttersprache
                        'user_level',             # Maximaler Level
                        'user_total_tries',       # Gesamtzahl versuche
                        'user_total_errors',      # Gesamtzahl Fehler
                        # user_total_tries_set
                        # user_total_tries_correct
                        # user_total_tries_explain
                        # .. das gleiche für _errors
                        #
                        #
                        #
                        #

                        'user_orthosem',          # participant_ortho_sem
                        ]

        count = 0

        for u in User.objects.all():
            if u.solution_set.count() == 0:
                continue
            row = []
            row.append(u.id)
            row.append(u.explicit_data_study())
            row.append(u.explicit_data_semester())
            row.append(u.explicit_data_subject1())
            row.append(u.explicit_data_subject2())
            row.append(u.explicit_data_subject3())
            row.append(u.explicit_data_study_permission())
            row.append(u.data_selfestimation)
            row.append(u.data_sex)
            row.append(u.data_l1)
            row.append(u.rules_activated_count)
            row.append(u.tries())
            row.append(u.errors())
            row.append(1 if u.data_orthosem_participant else 0)

            data.append(row)
            count += 1
            if count % 100 == 0:
                self.stdout.write('{} Zeilen erstellt'.format(count))

        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_users.xlsx', 'wb') as f:
            f.write(data.xlsx)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} users.'.format(count)))
