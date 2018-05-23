from django.core.management.base import BaseCommand, CommandError
from trainer.models import Rule, Sentence, SentenceRule
from django.db import transaction


class Command(BaseCommand):
    help = 'Read sentences.'

    def handle(self, *args, **options):

        Sentence.objects.filter(id__gte=160).update(active=True)
        x=Sentence.objects.filter(active=True)
        print(len(x))