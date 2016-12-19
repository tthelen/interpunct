from django.db import models
import re  # regex support
import random


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

    def get_commaselectlist(self):
        """
        Get the commatype list.
        :return: List of type values split at commas
        """
        return re.split(r'[,]+', self.comma_select.strip())

    def set_comma_select(self, user_select_str):
        """
        Set how much times certain comma was selected
        :param bitfield: user solution
        """
        selects = self.get_commaselectlist();
        user_select_arr = re.split(r'[,]+', user_select_str)
        for i in range(len(self.get_commalist())-1):
            if i != len(self.get_commalist()):
                selects[i] = str(int(selects[i]) + int(user_select_arr[i]))+ ","
            else:
                selects[i] = str(int(selects[i]) + int(user_select_arr[i]))
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
            # for each position: get rules
            mode = 0  # mustnot
            rules = self.sentencerule_set.filter(position=pos+1).all()
            for r in rules:
                if r.rule.mode == 1:
                    mode = 1
                elif r.rule.mode == 2: # must overrides any 'may'
                    mode = 2
                    break
            l.append(mode)
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

    def get_options(self, commatype):
        """
        :param commatype:
        :param difficulty: int 0,1,2,3 implement later
        :return:
        """
        index = random.randint(0, 3)
        solution = [0,0,0,0]
        count = Rule.objects.all().count()
        for i in range(4):
            if i != index:
                solution[i] = Rule.objects.all()[int(random.random() * count)]
            else:
                solution[i] = commatype
        return solution


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

class User(models.Model):
    user_id = models.CharField(max_length = 255)
    total_sentences = models.IntegerField
    # counts wrong answers for a specific comma type
    comma_type_false = models.CharField(max_length=400,default="KK:0, A1:0/0, A2:0/0, A3:0/0, A4:0/0, B1.1:0/0, B1.2:0/0, B1.3:0/0, B1.4.1:0/0, B1.4.2:0/0, B1.5:0/0, B2.1:0/0, B2.2:0/0, B2.3:0/0, B2.4.1:0/0, B2.4.2:0/0, B2.5:0/0, C1:0/0, C2:0/0, C3.1:0/0, C3.2:0/0, C4.1:0/0, C4.2:0/0, C5:0/0, C6.1:0/0, C6.2:0/0, C6.3.1:0/0, C6.3.2:0/0, C6.4:0/0, C7:0/0, C8:0, D1:0/0, D2:0/0, D3:0/0, E0:0/0")
    def get_dictionary(self):
        """
        Dictionary with comma types as keys and a value tuple of erros and total amount of trials
        :return: dictionary
        """
        type_dict = {}
        tmp = re.split(r'[ ,]+', self.comma_type_false)
        for elem in tmp:
            [a,b] = re.split(r':',elem)
            type_dict[a]=b
        return type_dict

    def save_dictionary(self,update):
        """
        Save updated dictionary to the database
        :param update: updated dictionary
        """
        new_dict_str = ""
        for key in update:
            new_dict_str += key + ":" + update[key] + ","
        self.comma_type_false = new_dict_str[:-1]
        self.save()

    def count_false_types(self, user_array, solution_array):
        """
        :param user_array: contains submitted array of bools
        :param solution_array: contains solution array with 0,1,2
        :return: ratio
        """

        dict = self.get_dictionary()
        for i in range(len(solution_array)-1, -1, -1):
            if solution_array[i] == [] and user_array[i] == 1:
                dict["KK"] += 1
            elif solution_array[i][0] != []:
                a, b = re.split(r'/', dict[solution_array[i]])
                rule= Rule.objects.get(code=solution_array[i][0])
                if rule.mode == 0 and user_array[i] != 0:                                   #must not, false
                    dict[solution_array[i][0]] = str(int(a)+1) + "/" + str(int(b) + 1)
                if rule.mode == 0 and user_array[i] == 0:                                   #must not, correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 1:                                                          #may, always correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 2 and user_array[i] == 1:                                   #must, correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 2 and user_array[i] == 0:                                   #must, false
                    dict[solution_array[i][0]] = str(int(a)+1) + "/" + str(int(b) + 1)
        self.save_dictionary(dict)
