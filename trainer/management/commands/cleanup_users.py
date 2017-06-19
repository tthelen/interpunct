from django.core.management.base import BaseCommand, CommandError
from trainer.models import User
from django.contrib.auth.models import User as DjangoUser

class Command(BaseCommand):
    help = 'Re-Imports the rule set.'

    def handle(self, *args, **options):

        count = 0
        for u in DjangoUser.objects.all():

            try:
                uu = User.objects.get(django_user=u)
            except User.DoesNotExist:
                if u.is_staff:
                    self.stdout.write("Not deleting staff {}".format(u))
                else:
                    self.stdout.write("deleting {}".format(u))
                    u.delete()
                    count += 1

        self.stdout.write(self.style.SUCCESS('Successfully cleaned up user db by deleting {} users.'.format(count)))
