from django.core.management.base import BaseCommand, CommandError
from trainer.models import User, UserRule, Rule
from django.core.exceptions import MultipleObjectsReturned

class Command(BaseCommand):
    help = 'Re-Imports the rule set.'

    def handle(self, *args, **options):

        count = 0
        for u in User.objects.all():
            rule_order = [
                "A1",  # 1 GLEICHRANG
                "A2",  # 2 ENTGEGEN
                "B1.1",  # 3 NEBEN
                "B2.1",  # 4 UMOHNESTATT
                "B1.2",  # 5 NEBENEINLEIT
                "B1.5",  # 6 FORMELHAFT
                "A3",  # 7 SATZREIHUNG
                "A4",  # 8 GLEICHRANG KONJUNKT
                "D1",  # 9 ANREDE/AUSRUF/STELLUNGNAHME
                "B2.2",  # 10 INF:VERWEIS
                "B2.3",  # 11 INF:EINFACH
                "B2.5",  # 12 INFP
                "C1",  # 13 HERAUSSTELLUNG
                "C6.2",  # 14 NACHTRAG
                "C3.1",  # 15 NOPRÄP
                "C3.2",  # 16 NOPRÄP:SCHLIESS
                "C6.1",  # 17 EIGENNAME:TITEL
                "C7",  # 18 EIGENNAME:KEINNACHTRAG
                "C8",  # 19 HINWEIS:GESETZ
                "B1.3",  # 20 NEBEN KONJUNKT
                "B1.4.1",  # 21 SUBORD:KOORD:KONJ:ADJAZ
                "B1.4.2",  # 22 SUBORD:KOORD:KONJ:NONADJAZ
            ]
            for userrule in UserRule.objects.filter(user=u):
                r = userrule.rule
                try:
                    ur = UserRule.objects.get(rule=Rule.objects.get(code=r), user=u)
                except MultipleObjectsReturned:
                    urs = UserRule.objects.filter(rule=Rule.objects.get(code=r), user=u)
                    urs[1].delete()
                    self.stdout.write(self.style.SUCCESS('Deleted duplicate rule {} for user {}'.format(r, u)))

        self.stdout.write(self.style.SUCCESS('Successfully cleaned up user db by deleting {} userrules.'.format(count)))
