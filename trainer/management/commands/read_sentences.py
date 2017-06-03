from django.core.management.base import BaseCommand, CommandError
from trainer.models import Rule, Sentence, SentenceRule
from django.db import transaction


class Command(BaseCommand):
    help = 'Read sentences.'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)
        # Named (optional) arguments
        parser.add_argument(
            '--deactivate',
            action='store_true',
            dest='deactivate',
            default=False,
            help='Deactivate all rules before importing new ones.',
        )

    def handle(self, *args, **options):

        if 'deactivate' in options:  # deactivate all sentences
            Sentence.objects.all().update(active=False)

        for fn in options['filename']:  # read all given files
            with open("sentences.txt", "r", encoding="utf-8") as f:
                for line in f:  # all lines in file
                    with transaction.atomic():  # all db actions as one transaction
                        shortcut_string=line.strip()
                        sentence, words, rules = self.from_shortcuts(shortcut_string)
                        print("Sentence: {}, Words: {}, Rules: {}".format(sentence, words, rules))
                        s = Sentence(text=sentence, active=True)
                        s.comma_select = ",".join(["0" for x in s.get_commalist()])
                        s.save()
                        for (pos,pair, r) in rules:
                            rs = SentenceRule(rule=r, sentence=s, position=pos, pair=pair)
                            rs.save()


    def from_shortcuts(self, shortcut_string):
        """Parse sentence shortcut notation.

        After each word a list of applicable rules can be inserted:

        Der (E1) Mann, (B1.1, A4, F4.3.2) der sich (E2) wundert.
        Ein Hund, (#1,B1.1) der bellt, (#1,B1.1) beißt nicht.

        Method returns:
        (sentence - cleared sentence,
        words - list of words,
        rules - Triples containing:
                (position - 0-based position in sentence,
                 pair - does comma belong to a comme pair (0=no, 1.. = yes, pair #1...)
                 rule - Rule object))
        """

        shortcut_string.replace('(,)',',') # treat MAY-commas indicated as (,) like , - the mode comes from the rules

        import shlex
        lexer = shlex.shlex(shortcut_string)
        lexer.wordchars += '-.äöüÜÖÄß?!"\'#'  # Make . in Rule code (B4.1 etc.) and pair inf o #1... parseable
        lexer.commenters = '' # no comments
        rules = []
        words = []
        sentence = ""
        state_in_ruleset = False
        position = 0
        pair = 0  # to which comma pair will subsequent positioned rules belong?
        while 1:
            token = lexer.get_token()
            if not token:
                break
            if token == '(':
                state_in_ruleset = True
            elif token == ')':
                state_in_ruleset = False
                pair = 0
            elif token == ',':
                # we ignore , for now since we don't need it (it's all in the rule names)
                if not state_in_ruleset:
                    sentence=sentence[:-1] # cut off last blank
                    sentence += ', '
            else:
                if state_in_ruleset:
                    # we found a rule
                    if token.startswith('#'): # pair info
                        pair = int(token[1:])
                    else:
                        try:
                            r = Rule.objects.get(code=token)
                            rules.append((position, pair, r))
                        except Rule.DoesNotExist:
                            pass
                else:
                    # we found a word
                    words.append(token)
                    sentence += token+" "
                    position += 1

        return (sentence, words, rules)