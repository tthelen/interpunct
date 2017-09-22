from django.core.management.base import BaseCommand, CommandError
from trainer.models import User, Sentence
from django.contrib.auth.models import User as DjangoUser

class Command(BaseCommand):

    help = 'Cleanup the data for evaluation.'

    def handle(self, *args, **options):

        count = 0

        # users to delete (Liste Hubert)
        for uid in [5,15,38,88,90,110,133,150,162,165,168,173,177,182,184,216,228,235,287,360,368,399,421,469,531,551,553,556]:
            try:
                u = User.objects.get(pk=uid)
                what = u.django_user.delete()  # delete the django user all other fields and relations will cascade
                print("User {} deleted. ({} object: {})".format(uid, what[0], what[1]))
            except User.DoesNotExist:
                print("User {} not found.".format(uid))

        for sid in [167,222,252,244,262,300,307,308,232]:
            try:
                s = Sentence.objects.get(pk=sid)
                what = s.delete()
                print("Sentence {} deleted. ({} object: {})".format(sid, what[0], what[1]))
            except Sentence.DoesNotExist:
                print("Sentence {} not found.".format(sid))

        self.stdout.write(self.style.SUCCESS('Successfully cleaned up db.'.format(count)))
