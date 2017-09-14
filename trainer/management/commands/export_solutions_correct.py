from django.core.management.base import BaseCommand
from trainer.models import User, Solution
import tablib


class Command(BaseCommand):

    help = 'Export all solutions to excel file.'

    def handle(self, *args, **options):

        data = tablib.Dataset()
        data.headers = ['solution_id',      # Solution.id
                        'sentence_id',      # Solution.sentence.id
                        'user_id',          # User.id
                        'rule_code',        # Rule.code
                        'rule_paragraph',   # Rule.rule
                        'correct',          # .correct
                        'left_context',     # built from .left
                        'comma_set',        # .commaset
                        'comma_presented',
                        'comma_correct',    # .commastring
                        'correction_type',  # explanation of correction
                        'correction_code',  # code of correction
                        'right_context',    # built from .right
                        'time',             # Solution.time_elapsed
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
                        'user_orthosem',          # participant_ortho_sem
                        ]

        count = 0

        for s in Solution.objects.all():

            sols = s.for_export_correct()

            for sol in sols:

                if sol['solution'].sentence.id in [167,262,222,244,252,262,300,307,308]:
                    print("Ignoring sentence #{}".format(sol['solution'].sentence.id))
                    continue

                row = []
                row.append(sol['solution'].id)
                row.append(sol['solution'].sentence.id)
                row.append(sol['user'].id)
                if sol['rule']:
                    row.append(sol['rule'].code)
                    row.append(sol['rule'].rule or sol['rule'].code)
                else:
                    row.append("")
                    row.append("")
                row.append(1 if sol['correct'] else 0)
                lc = "".join(["{}{}".format(w['word'], w['commaset']+(" " if w['commaset'] == ',' else ''))
                              for w in sol['left']]) + sol['word']
                row.append(lc)
                row.append(sol['commaset'])
                row.append(sol['commapresented'])
                row.append(sol['commastring'])
                row.append(sol['correction_type'])
                row.append(sol['correction_code'])
                rc = "".join(["{}{}".format(w['word'], w['commaset']+(" " if w['commaset'] == ',' else ''))
                              for w in sol['right'][:-1]]) + sol['right'][-1]['word']
                row.append(rc)
                row.append(sol['solution'].time_elapsed/1000.0)
                row.append(sol['user'].explicit_data_study())
                row.append(sol['user'].explicit_data_semester())
                row.append(sol['user'].explicit_data_subject1())
                row.append(sol['user'].explicit_data_subject2())
                row.append(sol['user'].explicit_data_subject3())
                row.append(sol['user'].explicit_data_study_permission())
                row.append(sol['user'].data_selfestimation)
                row.append(sol['user'].data_sex)
                row.append(sol['user'].data_l1)
                row.append(sol['user'].rules_activated_count)
                row.append(sol['user'].tries())
                row.append(sol['user'].errors())
                row.append(1 if sol['user'].data_orthosem_participant else 0)

                data.append(row)
                count += 1
                if count % 100 == 0:
                    self.stdout.write('{} Zeilen erstellt'.format(count))

        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_solutions_correct.xlsx', 'wb') as f:
            f.write(data.xlsx)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} solutions.'.format(count)))
