from django.core.management.base import BaseCommand
from trainer.models import User

class Command(BaseCommand):
    help = 'Debug info for user state.'

    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='+', type=str)

    def handle(self, *args, **options):

        print("Data for User {}".format(options['user_id']))
        u = User.objects.get(user_id=options['user_id'][0])
        s = u.get_strategy()
        o = s.debug_output()
        print(o)
