from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from trainer.models import Rule, User
import re

class Command(BaseCommand):
    help = 'Reads update rule set vom kommaregeln.csv'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--clean',   # name of the argument
            action='store_true',  # store value as True
            dest='clean',  # name of the attribute
            default=False,  # default value if not specified
            help='Delete all existing rules before importing (makes historical data useless)',  # help text
        )

    def handle(self, *args, **options):

        if options['clean']:
            Rule.objects.all().delete()
            # print warning
            self.stdout.write(self.style.WARNING('All existing rules deleted! Database is useless now and has to refreched completely.'))

            # delete all non-admin users
            User.objects.filter(django_user__is_superuser=False).delete()
            self.stdout.write(self.style.WARNING('All non-admin users deleted!'))

        import csv
        # read excel-created csv file
        with open('data/kommaregeln.csv', newline='', encoding='utf8') as csvfile:
            csvfile.readline()  # skip first line
            reader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in reader:
                if row[0] == '':    # empty line
                    continue    # skip  empty lines
                try:
                    r = Rule.objects.get(code=row[0])
                    self.stdout.write(self.style.SUCCESS('Update rule "%s"' % row[0]))
                except ObjectDoesNotExist:
                    r = Rule()
                    r.code = row[0]
                    self.stdout.write(self.style.SUCCESS('Create rule "%s"' % row[0]))
                r.mode = ['darf nicht', 'kann', 'muss'].index(row[1])
                r.description = row[2]
                r.rule = row[3]
                exs = "</p><p>".join(row[4:9])
                if exs:
                    r.example = "<p>"+exs+"</p>"
                else:
                    r.example = ""

                # replace kommas
                r.example = re.sub(r"\(,\)", "[,]", r.example)  # optional comma displayed as [,]
                r.example = re.sub(r"\([^)]+\)", "", r.example)  # remove all other rule parts
                r.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated rules.'))

