from django.core.management.base import BaseCommand
from trainer.models import User

class Command(BaseCommand):
    help = 'Import flag for participants of an orthography seminar.'

    def handle(self, *args, **options):

        count = 0
        with open("data/from_ortho_sem_final.csv","r") as f:
            for line in f:
                try:
                    u = User.objects.get(user_id=line.strip())
                    u.data_orthosem_participant = True
                    u.save()
                    count += 1
                except User.DoesNotExist:
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully imported {} orthography seminar user flags.'.format(count)))
