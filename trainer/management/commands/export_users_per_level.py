from django.core.management.base import BaseCommand
from trainer.models import User, Rule, Solution, SolutionRule
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
                        # 'user_tries_set',   # Gesamtzahl Versuche "Komma setzen"
                        # 'user_tries_correct', # Gesamtzahl Versuche "Komma korrigieren"
                        # 'user_tries_explain', # Gesamtzahl Versuche "Komma erklären"
                        # 'user_total_tries',       # Gesamtzahl versuche
                        # 'user_errors_set',
                        # 'user_errors_correct',
                        # 'user_errors_explain',
                        # 'user_total_errors',      # Gesamtzahl Fehler
                        'user_orthosem',          # participant_ortho_sem
                        'error_ratio',
                        'level01',
                        'level02',
                        'level03',
                        'level04',
                        'level05',
                        'level06',
                        'level07',
                        'level08',
                        'level09',
                        'level10',
                        'level11',
                        'level12',
                        'level13',
                        'level14',
                        'level15',
                        'level16',
                        'level17',
                        'level18',
                        'level19',
                        'level20',
                        'level21',
                        'level22',
                        'level23',
                        'level24',
                        'level25',
                        'level26',
                        'level27',
                        'level28',
                        'level29',
                        'level30',
                        # user_total_tries_set
                        # user_total_tries_correct
                        # user_total_tries_explain
                        # .. das gleiche für _errors
                        #
                        #
                        #
                        #

                        ]

        count = 0

        rule_order = [
            "A1",  # 1 GLEICHRANG
            "A2",  # 2 ENTGEGEN
            "B1.1",  # 3 NEBEN
            "B2.1",  # 4 UMOHNESTATT
            "C1",  # 5 PARANTHESE
            "D1",  # 6 ANREDE/AUSRUF
            "B1.2",  # 7 NEBEN EINLEIT
            "C2",  # 8 APPOSITION
            "A3",  # 9 SATZREIHUNG
            "C5",  # 10 HINWEIS
            "B1.5",  # 11 FORMELHAFT
            "A4",  # 12 GLEIHRANG KONJUNKT
            "D3",  # 13 BEKTRÄFT
            "B2.2",  # 14
            "C3.1",  # 15
            "B2.3",  # 16
            "C3.2",  # 17
            "B2.4.1",  # 18
            "C4.1",  # 19
            "B2.4.2",  # 20
            "B2.5",  # 21
            "C6.1",  # 22
            "C6.2",  # 23
            "C6.3.1",  # 24
            "C6.3.2",  # 25
            "C6.4",  # 26
            "C7",  # 27
            "B1.3",  # 28 NEBEN KONJUNKT
            "B1.4.1",  # 29
            "B1.4.2",  # 30
        ]

        for u in User.objects.all():
            if u.solution_set.count() == 0:
                continue
            if u.rules_activated_count < 30:  # only participants who reached level 30
                continue
            row = list()
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
            # row.append(u.tries(type='set'))
            # row.append(u.tries(type='correct'))
            # row.append(u.tries(type='explain'))
            # row.append(u.tries())
            # row.append(u.errors(type='set'))
            # row.append(u.errors(type='correct'))
            # row.append(u.errors(type='explain'))
            # row.append(u.errors())
            row.append(1 if u.data_orthosem_participant else 0)

            row.append(float(u.errors())/float(u.tries()))  # error ratio

            for r in rule_order:
                rule = Rule.objects.get(code=r)
                tries = u.tries(rule=rule)
                errors = u.errors(rule=rule)
                print("Rule {}: {} errors/ {} tries".format(rule.code, errors, tries))
                row.append(float(errors)/float(tries) if tries else 0.0)
            data.append(row)
            count += 1
            if count % 100 == 0:
                self.stdout.write('{} Zeilen erstellt'.format(count))

        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_users_per_level.xlsx', 'wb') as f:
            f.write(data.xlsx)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} users.'.format(count)))
