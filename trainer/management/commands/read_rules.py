from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from trainer.models import Rule


class Command(BaseCommand):
    help = 'Reads update rule set vom kommaregeln.csv'

    def handle(self, *args, **options):
        from tablib import Dataset
        imported_data = Dataset().load(open('kommaregeln.csv', encoding='utf-8').read())
        for row in imported_data:
            try:
                r = Rule.objects.get(code=row[0])
                self.stdout.write(self.style.SUCCESS('Update rule "%s"' % row[0]))
            except ObjectDoesNotExist:
                r = Rule()
                r.code = row[0]
                self.stdout.write(self.style.SUCCESS('Create rule "%s"' % row[0]))
            r.slug = row[1]
            r.mode = ['darf nicht', 'kann', 'muss'].index(row[2])
            r.description = row[3]
            r.rule = row[4]
            r.example = row[6]
            import re
            r.example=re.sub(r"\([^,].*\)","",r.example)
            r.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated rules.'))

