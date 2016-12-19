from django.db import models
import re  # regex support



class Rule(models.Model):
    """
    Represents a rule for mandatory, discretionay, prohibited commas, including typical errors.
    """

    MODES = (
        (0, 'darf nicht'),
        (1, 'kann'),
        (2, 'muss'),
    )

    code = models.CharField(max_length=32)
    slug = models.SlugField(max_length=128)
    mode = models.IntegerField(choices=MODES)
    description = models.CharField(max_length=2048)
    rule = models.CharField(max_length=255)
    # example1 = django.db.models.ForeignKey('Sentence')
    # example2 = django.db.models.ForeignKey('Sentence')
    # example3 = django.db.models.ForeignKey('Sentence')

    def __str__(self):
        return self.code


class Sentence(models.Model):
    """
    Represents one sentence.
    Database representation has to include correct commas.
    The sentence is stored as a string in the database,
    words are separated by blanks and commas.

    text: Complete text with commas. (TODO: without commas?)
    comma_list: int list of comma types (TODO: replaced by rules)
    comma_select: int list of how often comma was set here
    total_submits: number of tries for sentence
    rules: n:m relation to Rule through SentenceRule table (adding position)

    IMPORTANT: The list of words of a sentence must never change!
               Solutions store a bool value for each gap, so gap
               positions must stay fixed.

    Example: Wir essen, Opa.
    """
    text = models.CharField(max_length=2048)
    #comma_list = models.CommaSeparatedIntegerField(max_length=255, default='0')
    comma_select = models.CommaSeparatedIntegerField(max_length=255, default='0')
    total_submits = models.IntegerField(max_length=25, default='0')  #
    rules = models.ManyToManyField(Rule, through='SentenceRule')

    def __str__(self):
        return self.text

    def update_submits(self):
        self.total_submits += 1
        self.save()

    def get_commaselectlist(self,user):
        """
        Get the commatype list.
        :return: List of type values split at commas
        """
        return (re.split(r'[,]+', self.comma_select.strip()),re.split(r'[,]+', user.strip()))

    def set_comma_select(self, user_select):
        """
        Set how much times certain comma was selected
        :param bitfield: user solution
        """
        selects,user_selects = self.get_commaselectlist(user_select);
        if len(selects) == 1:
            for i in range(len(self.get_commalist())-1):
                selects.append(0)
        for i in range(len(self.get_commalist())):
            selects[i] = str(int(selects[i]) + int(user_selects[i]))

        self.comma_select = "".join(selects)
        self.save()

    def get_words(self):
        """
        Get the word list.
        :return: List of words split at blanks or commas
        """
        return re.split(r'[ ,]+', self.text.strip())

    def get_commalist(self):
        """
        Where do the commas go?
        :return: List of boolean values indicating comma/no comma at that position.
        """
        l = []  # list of comma types (0=mustnot, 1=may, 2=must)
        for pos in range(len(self.get_words())-1):
            print("length: %d " % (len(self.get_words())))
            print("Position : %d" % pos)
            # for each position: get rules
            mode = 0  # mustnot
            rules = self.sentencerule_set.filter(position=pos+1).all()
            print("Amount of rules %d." % (len(rules)))
            for r in rules:
                print("Rule.Mode %s." % (r.rule.mode))
                if r.rule.mode == 1:
                    mode = 1
                elif r.rule.mode == 2: # must overrides any 'may'
                    mode = 2
                    break
            l.append(mode)
            print(l)
        return l

    def get_commatypelist(self):
        """
        Return a list of rule-name-lists for each position in the sentence.
        :return: List of lists with rule names.
        """
        l = []  # list of comma types (0=mustnot, 1=may, 2=must)

        for pos in range(len(self.get_words())):
            # print("Position is %d" % pos)
            # for each position: get rules
            rules = self.rules.filter(sentencerule__position=pos+1).all()
            rl = []
            for r in rules:
                rl.append(r.code)  # collect codes, not rules objects
            l.append(rl)
        return l

    def get_commaval(self):
        """
        Where do the commas go?
        :return: Bitfield (integer) indicating comma/no comma at that position.
        """
        val = 0
        commas = self.get_commalist()
        for i in range(len(commas)):
            if commas[i]:
                val += 2 ** i
        return val


class SentenceRule(models.Model):

    """
    Intermediate model for ManyToMany-Relationship of Sentences and Rules.

    Position indicates the 0-based position in the sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    position = models.IntegerField()

    def __str__(self):
        return self.sentence.text + self.rule.code

class Solution(models.Model):
    """
    Represents one solutions to a sentence.
    Solutions are stored as bitfields for a sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    # We do not use django users here because the user id is provided by the embedding system
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255)
    solution = models.BigIntegerField()