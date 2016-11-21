from django.core.management.base import BaseCommand, CommandError
from trainer.models import Rule, Sentence, SentenceRule


class Command(BaseCommand):
    help = 'Read sentences.'

    def handle(self, *args, **options):
        with open("sentences.txt", "r", encoding="utf-8") as f:
            while 1:
                shortcut_string=f.readline().strip()
                if not shortcut_string:
                    break
                sentence, words, rules = self.from_shortcuts(shortcut_string)
                s = Sentence(sentence)
                s.save()
                for (p,r) in rules:
                    rs = SentenceRule(rule=r, sentence=s, position=p)
                    rs.save()


    def from_shortcuts(self, shortcut_string):
        """Parse sentence shortcut notation.

        After each word a list of applicable rules can be inserted:

        Der (E1) Mann, (B1.1, A4, F4.3.2) der sich (E2) wundert.

        Method returns:
        (sentence - cleared sentence,
        words - list of words,
        rules - Tuples containing:
                (position - 0-based position in sentence,
                 rule - Rule object))
        """

        import shlex
        lexer = shlex.shlex(shortcut_string)
        lexer.wordchars += '.'  # Make . in Rule code (B4.1 etc.) parseable

        rules = []
        words = []
        sentence = ""
        state_in_ruleset = False
        position = 0
        while 1:
            token = lexer.get_token()
            if not token:
                break
            if token == '(':
                state_in_ruleset = True
            elif token == ')':
                state_in_ruleset = False
            elif token == ',':
                # we ignore , for now since we don't need it (it's all in the rule names)
                # TODO: discuss what we can do with given , in the sentence
                if not state_in_ruleset:
                    sentence=sentence[:-1] # cut off last blank
                    sentence += ', '
            else:
                if state_in_ruleset:
                    # we found a rule
                    try:
                        r = Rule.objects.get(code=token)
                        rules.append((position, r))
                    except Rule.DoesNotExist:
                        pass
                else:
                    # we found a word
                    words.append(token)
                    sentence += token+" "
                    position += 1

        return (sentence, words, rules)