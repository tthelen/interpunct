from django.core.management.base import BaseCommand
from trainer.models import User, Solution, Sentence
import tablib


class Command(BaseCommand):

    help = 'Export all solutions to excel file.'

    def handle(self, *args, **options):

        data = tablib.Dataset()
        data.headers = ['sentence_id',      # Sentence.id
                        'sentence',         # satz
                        'solutions',        # anzahl lösungen (typ1)
                        'false_variants',   # anzahl verschiedener falscher lösungen (typ1)
                        ]

        count = 0

        for s in Sentence.objects.filter(active=True).all():

            if s.id in [167,262,222,244,252,262,300,307,308]:
                continue

            row = []
            row.append(s.id)
            row.append(s.text)
            row.append(s.count_set_solutions())

            false_variants = 0
            for sfr in s.for_render():
                if not sfr['render'][0]['solution_correct']:
                    false_variants += 1
            row.append(false_variants)


            data.append(row)
            count += 1
            if count % 100 == 0:
                self.stdout.write('{} Zeilen erstellt'.format(count))

        self.stdout.write("Schreibe XLSX-Datei")
        with open('data/output_sentences.xlsx', 'wb') as f:
            f.write(data.xlsx)

        self.stdout.write(self.style.SUCCESS('Successfully exported {} sentences.'.format(count)))
