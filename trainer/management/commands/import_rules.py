from django.core.management.base import BaseCommand, CommandError
from trainer.models import Rule

class Command(BaseCommand):
    help = 'Re-Imports the rule set.'

    def handle(self, *args, **options):
        from tablib import Dataset
        imported_data = Dataset().load(open('kommaregeln.csv', encoding='utf-8').read())
        # Rule.objects.all().delete()  # Delete all rules. TODO: Build update mechanism
        for row in imported_data:
            r=Rule.objects.get(code=row[0])
            if not r:  # rule with this code does not yet exist: create!
                r = Rule()
                r.code = row[0]
                self.stdout.write(self.style.SUCCESS('Rule {} created.').format(r.code))
            else:
                self.stdout.write(self.style.SUCCESS('Rule {} updated.').format(r.code))
            r.slug = row[1]
            r.mode = ['muss', 'kann', 'darf nicht'].index(row[2])
            r.description = row[3]
            r.rule = row[4]
            r.save()
        self.stdout.write(self.style.SUCCESS('Successfully imported rules.'))
