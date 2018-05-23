from django.core.management.base import BaseCommand, CommandError
from trainer.models import Rule, Sentence, SentenceRule
from django.db.models import Count


class Command(BaseCommand):
    help = 'Tests some code.'

    def handle(self, *args, **options):

        print("Sentences for B1.2:")
        r=Rule.objects.get(code="B1.2")
        possible_sentences = SentenceRule.objects.filter(rule=r, sentence__active=True).annotate(
            rule_count=Count('sentence__rules')).order_by('rule_count')
        for ps in possible_sentences:
            print(len(ps.sentence.rules.all()), ps.sentence.rules.all(), ps.sentence)