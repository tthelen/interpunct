from django.db import models
import re  # regex support


class Rule(models.Model):
    """
    Represents a rule for mandatory, discretionay, prohibited commas, including typical errors.
    """

    MODES = (
        (0, 'mustnot'),
        (1, 'may'),
        (2, 'must'),
    )

    code = models.CharField(max_length=32)
    slug = models.SlugField(max_length=128)
    mode = models.IntegerField(choices=MODES)
    description = models.CharField(max_length=2048)
    rule = models.CharField(max_length=255)
    # example1 = django.db.models.ForeignKey('Sentence')
    # example2 = django.db.models.ForeignKey('Sentence')
    # example3 = django.db.models.ForeignKey('Sentence')


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
    comma_list = models.CommaSeparatedIntegerField(max_length=255, default='0')
    comma_select = models.CommaSeparatedIntegerField(max_length=255, default='0')
    total_submits = models.IntegerField(max_length=25, default='0')  #
    rules = models.ManyToManyField(Rule, through='SentenceRule')

    def __str__(self):
        return self.text

    def update_submits(self):
        self.total_submits += 1
        self.save()

    def set_default_commalist(self):
        """
        Set default list of comma types: amout of zeros = amount of comma-slots
        """
        self.comma_list
        for i in range(len(self.get_commalist())):
            self.comma_list.append(',0')

    def set_comma_select(self, bitfield):
        """
        TODO: Documentation! What's this method for?
        :param bitfield:
        :return:
        """
        comma_select = self.get_commaselectlist()
        for i in range(len(comma_select) - 1, -1, -1):
            if (bitfield - 2 ** i >= 0) & (i != (len(comma_select) - 1)):
                comma_select[i] = str(int(comma_select[i]) + 1) + ","
                bitfield -= 2 ** i
            elif bitfield - 2 ** i >= 0:
                comma_select[i] = str(int(comma_select[i]) + 1)
                bitfield -= 2 ** i
            elif i != (len(comma_select) - 1):
                comma_select[i] += ","

        self.comma_select = "".join(comma_select)
        self.save()

    def get_commaselectlist(self):
        """
        Get the commatype list.
        :return: List of type values split at commas
        """
        return re.split(r'[,]+', self.comma_select.strip())

    #def get_commatypelist(self):
    #    """
    #    Get the commatype list.
    #    :return: List of type values split at commas
    #    """
    #    return re.split(r'[,]+', self.comma_list.strip())

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
        l = []  # list of comma types (0=no, 1=may, 2=must)
        mode = 0
        for pos in range(len(self.get_words())):
            # for each position: get rules
            rules = self.sentencerule_set.filter(sentencerule__position=pos).all()

            mode = 0  # mustnot
            for r in rules:
                if r.rule.mode == 'may':
                    mode = 1
                elif r.rule.mode == 'must': # must overrides any 'may'
                    mode = 2
                    break
            l.append(mode)
        return l


    def get_commatypelist(self):
        """
        Return a list of rule-name-lists for each position in the sentence.
        :return: List of lists with rule names.
        """
        l = []  # list of comma types (0=no, 1=may, 2=must)

        print("Commtypelist... for %d words." % (len(self.get_words())))
        for pos in range(len(self.get_words())):
            # print("Position is %d" % pos)
            # for each position: get rules
            rules = self.rules.filter(sentencerule__position=pos).all()
            rl = []
            for r in rules:
                rl.append(r.code)  # collect codes, not rules objects
            l.append(rl)
        return l

        #return list(map(lambda x: ',' in x, re.split(r'\w+', self.text.strip())[1:-1]))

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
    """Intermediate model for ManyToMany-Relationship of Sentences and Rules.

    Position indicates the 0-based position in the sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    position = models.IntegerField()


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