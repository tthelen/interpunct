from django.db import models
from django.contrib.auth.models import User as DjangoUser
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
    example = models.CharField(max_length=2048, default='')
    # example1 = django.db.models.ForeignKey('Sentence')
    # example2 = django.db.models.ForeignKey('Sentence')
    # example3 = django.db.models.ForeignKey('Sentence')

    def __str__(self):
        return self.code

    def decode(self):
        decode_list = []
        for i in self.code:
            if i != ".":
                decode_list.append(i)
        while len(decode_list) != 4:
            decode_list.append("0")
        return decode_list

    def encode(self, decode_list):
        encode_list = ""
        for i in range(len(decode_list)):
            if i >= 1 and i != len(decode_list)-1 and decode_list[i] != '0' and decode_list[i+1] != '0':
                encode_list += str(decode_list[i]) + "."
            elif decode_list[i] != "0":
                encode_list += str(decode_list[i])
        return encode_list


class Sentence(models.Model):
    """
    Represents one sentence.
    Database representation has to include correct commas.
    The sentence is stored as a string in the database,
    words are separated by blanks and commas.

    text: Complete text with commas. (TODO: without commas?)
    comma_list: int list of comma types (TODO: replaced by rules)
    total_submits: number of tries for sentence
    rules: n:m relation to Rule through SentenceRule table (adding position)

    IMPORTANT: The list of words of a sentence must never change!
               Solutions store a bool value for each gap, so gap
               positions must stay fixed.

    Example: Wir essen, Opa.
    """
    text = models.CharField(max_length=2048)
    total_submits = models.IntegerField(default='0')  #
    rules = models.ManyToManyField(Rule, through='SentenceRule')
    active = models.BooleanField(default=True)

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
        return [] # re.split(r'[,]+', self.comma_select.strip())

    def set_comma_select(self, user_select_str):
        """
        Set how much times certain comma was selected
        :param boolean_str: string of seleced commas
        """
        return

        #selects = self.get_commaselectlist();
        #user_select_arr = re.split(r'[,]+', user_select_str)
        #for i in range(len(self.get_commalist())):
        #    if i != len(self.get_commalist())-1:
        #        selects[i] = str(int(selects[i]) + int(user_select_arr[i])) + ","
        #    else:
        #        selects[i] = str(int(selects[i]) + int(user_select_arr[i]))
        #self.comma_select = "".join(selects)
        #self.save()

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

        for pos in range(len(self.get_words())-1):
            # for each position: get rules
            rules = self.rules.filter(sentencerule__position=pos+1).all()
            rl = []
            for r in rules:
                rl.append(r.code)  # collect codes, not rules objects
            l.append(rl)
        return l

    def get_commapairlist(self):
        """
        Return a list of comma pair ids for each position in the sentence (0=does not beling to a pair.
        :return: List of integers.
        """
        l = []  # list of comma types (0=mustnot, 1=may, 2=must)

        for pos in range(len(self.get_words())-1):
            # for each position: get rules
            sr = SentenceRule.objects.filter(sentence=self, position=pos+1)
            pair = 0
            if sr:
                pair = sr[0].pair
            l.append(pair)
        return l

    def get_words_commas_rules(self):
        """Return a list of tuples: (word,commstring,rule) for a sentence."""

        words = self.get_words()

        rules = []  # list of comma types (0=mustnot, 1=may, 2=must)

        for pos in range(len(self.get_words()) - 1):
            # for each position: get rules
            ruleset = self.rules.filter(sentencerule__position=pos + 1).all()
            rl = []
            for r in ruleset:
                if not r.code=='E1':
                    rl.append(r)  # collect codes, not rules objects
            rules.append(rl)
        rules.append([])

        commas = []
        for r in rules:
            if not r or r[0].mode == 0:  # no mixed mode rules
                commas.append(" ")
            elif r[0].mode == 1:
                commas.append("(,) ")
            elif r[0].mode == 2:
                commas.append(", ")
        commas.append("")

        return list(zip(words,commas,rules))

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

    def get_explanations(self, commatype, user):
        """
        :param commatype: current type
        :param user: user rank
        :return: solution
        """

        rank = user.user_rank
        # Rule Representation: e.g : A,1,0,0 and Difference List
        rule_obj = Rule.objects.get(code=commatype)
        decode_list = rule_obj.decode()
        rule_list = Rule.objects.exclude(code__startswith='E').all()

        rule_decoded_list = []
        for rule in rule_list:
            rule_decoded_list.append(rule.decode())
        rule_decoded_list.remove(decode_list)

        # Initial Indexing, current commatype
        index_list = [0, 1, 2]
        index = random.choice(index_list)
        index_list.remove(index)

        solution = [0, 0, 0]
        count = Rule.objects.exclude(code__startswith='E').count()

        # Random Explanations
        for i in range(3):
            if i != index:
                tmp = random.choice(rule_decoded_list)
                solution[i] = Rule.objects.get(code=rule_obj.encode(tmp)).description
                rule_decoded_list.remove(tmp)
            else:
                solution[i] = rule_obj.description
        return solution, index


class SentenceRule(models.Model):

    """
    Intermediate model for ManyToMany-Relationship of Sentences and Rules.

    Position indicates the 0-based position in the sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    position = models.IntegerField()
    pair = models.IntegerField(default=0)  # if != 0: comma pair which this comma is part of

    def __str__(self):
        return "Rule {} at #{}: {} (Pair {})".format(self.rule.code, self.position, self.sentence.text, self.pair)



class User(models.Model):
    def __str__(self):
        return self.user_id

    RANKS = (
        (0, 'Kommachaot'),
        (1, 'Kommakönner'),
        (2, "Kommakommandant"),
        (3, 'Kommakönig'),
    )

    abschluss = {0: "Nicht angegeben",
                 10: "Bachelor BEU(Lehramt GHR)",
                 11: "Bachelor berufliche Bildung(Lehramt LBS)",
                 12: "Bachelor 2-Fächer (Lehramt Gym)",
                 13: "Bachelor 2- Fächer (kein Lehramt)",
                 14: "Bachelor (1 Fach)",
                 20: "Master(Lehramt GHR)",
                 21: "Master(Lehramt Gym)",
                 22: "Master(Lehramt LBS)",
                 23: "Master(kein Lehramt)",
                 30: "sonstiges",
                 40: "nicht studierend"}

    user_id = models.CharField(max_length = 255)

    data = models.CharField(max_length=255, default='')

    data_study = models.IntegerField(default=0)
    data_semester = models.IntegerField(default=0)
    data_subject1 = models.IntegerField(default=0)
    data_subject2 = models.IntegerField(default=0)
    data_subject3 = models.IntegerField(default=0)
    data_study_permission = models.IntegerField(default=0)
    data_sex = models.CharField(max_length=2, default='')
    data_l1 = models.CharField(max_length=255, default='')
    data_selfestimation = models.IntegerField(default=0)

    user_rank = models.IntegerField(choices=RANKS, default = 0)
    # counts wrong answers for a specific comma type
    comma_type_false = models.CharField(max_length=400,default="A1:0/0, A2:0/0, A3:0/0, A4:0/0, B1.1:0/0, B1.2:0/0, B1.3:0/0, B1.4.1:0/0, B1.4.2:0/0, B1.5:0/0, B2.1:0/0, B2.2:0/0, B2.3:0/0, B2.4.1:0/0, B2.4.2:0/0, B2.5:0/0, C1:0/0, C2:0/0, C3.1:0/0, C3.2:0/0, C4.1:0/0, C4.2:0/0, C5:0/0, C6.1:0/0, C6.2:0/0, C6.3.1:0/0, C6.3.2:0/0, C6.4:0/0, C7:0/0, C8:0/0, D1:0/0, D2:0/0, D3:0/0, E1:0/0")
    sentences = models.ManyToManyField(Sentence, through='UserSentence')

    # global exercise counter
    counter = models.IntegerField(default=0)
    counter_correct = models.IntegerField(default=0)
    counter_wrong = models.IntegerField(default=0)

    # rules_activated: user progress in terms of available rules.
    # Starts at 0, continues to ~40
    rules_activated_count = models.IntegerField(default=0)
    rules = models.ManyToManyField(Rule, through='UserRule')

    django_user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE, default=None)

    rule_order = [
        "A1",  # 1 GLEICHRANG
        "A2",  # 2 ENTGEGEN
        "B1.1",  # 3 NEBEN
        "B2.1",  # 4 UMOHNESTATT
        "C1",  # 5 PARANTHESE
        "D1",  # 6 ANREDE/AUSRUF
        "B1.2",  # 7 NEBEN EINLEIT
        "C2",  # 8 APPOSITION
        "A3",  # 9 SATZREIHUNG
        "C5",  # 10 HINWEIS
        "B1.5",  # 11 FORMELHAFT
        "A4",  # 12 GLEIHRANG KONJUNKT
        "D3",  # 13 BEKTRÄFT
        "B2.2",  # 14
        "C3.1",  # 15
        "B2.3",  # 16
        "C3.2",  # 17
        "B2.4.1",  # 18
        "C4.1",  # 19
        "B2.4.2",  # 20
        "B2.5",  # 21
        "C6.1",  #22
        "C6.2",  # 23
        "C6.3.1",  # 24
        "C6.3.2",  # 25
        "C6.4",  # 26
        "C7",  # 27
        "B1.3",  # 28 NEBEN KONJUNKT
        "B1.4.1",  # 29
        "B1.4.2",  # 30
    ]

    def update_rank(self):
        rank_counter = 0
        dict = self.get_dictionary()
        for key in dict:
            if key != "E1":
                a, b = re.split(r'/', dict[key])
                points = int(b)-int(a)
                if points >= 50:
                    rank_counter +=4
                if points >= 25:
                    rank_counter +=2
                if  points >= 10:
                    rank_counter +=1
        if rank_counter == len(dict)-1:
            self.user_rank = 1
            self.save()
        if rank_counter == 2 * (len(dict)-1):
            self.user_rank = 2
            self.save()
        if rank_counter == 4 * (len(dict) - 1):
            self.user_rank = 3
            self.save()

    def init_rules(self):
        """Initialize active rules for user."""

        # create correct rules
        for r in self.rule_order:
            ur = UserRule(rule=Rule.objects.get(code=r), user=self, active=False)
            ur.save()
        # create error rules
        ur = UserRule(rule=Rule.objects.get(code="E1"), user=self, active=False)
        ur.save()
        ur = UserRule(rule=Rule.objects.get(code="E2"), user=self, active=False)
        ur.save()

        # activate first rule
        new_rule = Rule.objects.get(code=self.rule_order[0])
        ur = UserRule.objects.get(rule=new_rule, user=self)
        ur.active = True
        ur.save()

        self.rules_activated_count = 1  # activate first rule for next request
        self.save()

        return new_rule

    def prepare(self, request):
        # create a real django user
        self.django_user = DjangoUser.objects.create_user(self.user_id, 'tobias.thelen@uni-osnabrueck.de', 'nopass')

    def login(self, request):
        """Login the corresponding django user."""
        from django.contrib.auth import login as django_user_login
        django_user_login(request, self.django_user)
        return True

    def progress(self):
        """Advance to next level, if appropriate.
        
        Returns (new_rule, finished?) 
        new_rule is False if no level progress, the newly activated Rule object otherwise.
        finished is false if not all rules are activated and true if all Rules are activated
        """

        # highest level reached?
        if self.rules_activated_count == len(self.rule_order):
            return (False, True)

        # d = self.get_dictionary()
        last_rule = self.rule_order[self.rules_activated_count - 1]
        ur = UserRule.objects.get(user=self, rule=Rule.objects.get(code=last_rule))
        # advancement criterion: at least 3 tries, less than half of them wrong
        # print("CHECK FOR PROGRESS: {},{},{}".format(ur.rule.code, ur.total, ur.correct))
        if ur.total >= 4 and ur.correct >= (ur.total / 2):
            self.rules_activated_count += 1
            self.save()
            # create and activate new rule for user
            new_rule = Rule.objects.get(code=self.rule_order[self.rules_activated_count - 1])
            new_ur = UserRule.objects.get(rule=new_rule, user=self)
            new_ur.active = True
            new_ur.save()
            return (new_rule, (self.rules_activated_count == len(self.rule_order)))

        return (False, False)

    def current_rule(self):
        if self.rules_activated_count == len(self.rule_order):
            return False
        return Rule.objects.get(code=self.rule_order[self.rules_activated_count - 1])

    def level_display(self):
        """Return UserRule and examples sentence data for displaying level and expanations. At most 5 rules sorted by box position."""

        limit = min(self.rules_activated_count, 5)
        res = UserRule.objects.filter(user=self, active=1).order_by('box')[:limit]
        return res


    def count(self, correct):

        self.counter += 1
        if correct:
            self.counter_correct += 1
        else:
            self.counter_wrong += 1


    def get_dictionary(self, only_activated=False):
        """
        Dictionary with comma types as keys and a value tuple of erros and total amount of trials
        :return: dictionary
        """
        type_dict = {}
        tmp = re.split(r'[ ,]+', self.comma_type_false)

        activated_rules = self.rule_order[:self.rules_activated_count]
        for elem in tmp:
            [a,b] = re.split(r':',elem)
            if not only_activated or a in activated_rules:
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

    def eval_set_commas(self, user_array_str, sentence, solution):
        """
        count false types for: AllKommaSetzen
        :param user_array: contains submitted array of bools
        :param solution_array: contains comma types
        :param solution The Solution object
        :return List of Dictionaries for each position: {correct:Boolean, rule:Rule}
        """
        resp = []
        solution_array = sentence.get_commatypelist()
        pairs = sentence.get_commapairlist()
        user_array = re.split(r'[ ,]+', user_array_str)
        for i in range(len(solution_array)):
            if len(solution_array[i]) == 0 and int(user_array[i]) == 1: # comma in the wild
                rule = Rule.objects.get(code="E1")
                try:
                    userrule = UserRule.objects.get(user=self, rule=rule)
                except UserRule.DoesNotExist:
                    userrule = UserRule(user=self, rule=rule)
                userrule.count(correct=False)
                resp.append({'correct':False,  'rule': {'code': rule.code, 'mode': rule.mode}})
                SolutionRule(solution=solution, rule=rule, error=True).save()  # save rule to solution
            elif len(solution_array[i]) != 0: # comma at rule position
                rules = Rule.objects.filter(code=solution_array[i][0])
                first = True  # save response in first run
                for rule in rules:
                    try:
                        userrule = UserRule.objects.get(user=self, rule=rule)
                    except UserRule.DoesNotExist:
                        userrule = UserRule(user=self, rule=rule).save()
                    if (rule.mode == 0 and user_array[i] == "0") or  \
                       (rule.mode == 2 and user_array[i] == "1"):
                        corr = True
                    elif rule.mode == 1: # optional commas - consider pairs!
                        if pairs[i] != 0: # if comma is part of a pair
                            # first part is always correct
                            # second part is the error
                            found = False
                            if i > 0:
                                for j in range(i):  # look at the beginning of the sentence to find 1st part of pair
                                    if pairs[j] == pairs[i]:
                                        corr = (user_array[i] == user_array[j])
                                        found = True
                                        break
                            if not found: # first occurence is always correct
                                corr = True
                        else:
                            corr = True
                    else:
                        corr = False
                    if first: # save response only for first rule (others must be same)
                        resp.append({'correct': corr,  'rule': {'code': rule.code, 'mode': rule.mode}})
                        first = False
                    userrule.count(correct=corr)
                    if not rule.code.startswith('E'): # count everything but error positions
                        self.count(corr)
                        self.save()
                    if not corr:
                        SolutionRule(solution=solution, rule=rule, error=True).save()  # save rule to solution
            else:
                resp.append({'correct': True, 'rule': {'code':'', 'mode':0}})
        return resp

    def count_false_types_task_correct_commas(self, user_array_str, sentence, solution):
        """
        count false types for: AllKommaSetzen
        :param user_array_str: contains submitted array of 2-bool-strings
        :param sentence: the sentence object
        :param solution: the solution object
        """
        user_array = re.split(r'[ ,]+', user_array_str) # contais pairs of (comma present / marked), e.g. 00, 01, 10, 11
        solution_array = sentence.get_commatypelist()  # for every position: rules for that position
        pairs = sentence.get_commapairlist()
        resp = []

        for i in range(len(solution_array)):

            if len(solution_array[i]) == 0: # non-rule position

                if user_array[i] == '11':  # wrong comma without rule detected correctly
                    resp.append({'correct': True, 'rule': {'code': '', 'mode': 0}})
                elif user_array[i] == '00': # no comma and not marked: ok
                    resp.append({'correct': True, 'rule': {'code': '', 'mode': 0}})
                else:  # wrong comma without rule not detected correctly or no-comma position marked
                    rule = Rule.objects.get(code="E1")
                    userrule = UserRule.objects.get(user=self, rule=rule)
                    userrule.count(correct=False)
                    resp.append({'correct': False, 'rule': {'code': rule.code, 'mode': rule.mode}})
                    SolutionRule(solution=solution, rule=rule, error=True).save()  # save rule to solution

            elif len(solution_array[i]) != 0: # rule position

                rules = Rule.objects.filter(code=solution_array[i][0])
                first = True  # save response in first run
                for rule in rules:

                    try:
                        userrule = UserRule.objects.get(user=self, rule=rule)
                    except UserRule.DoesNotExist:
                        userrule = UserRule(user=self, rule=rule)

                    # case 1: mode = 2 (MUST)
                    if rule.mode == 2:
                        corr = user_array[i] in ['01','10']  # right if set and not marked (and vice versa)

                    # case 2: mode = 1 (MAY)
                    if rule.mode == 1:
                        # handle unbalanced MAY commas
                        if pairs[i] != 0: # if comma is part of a pair
                            # first part is always incorrect
                            # second part might be correct
                            found = False
                            if i > 0:
                                for j in range(i):  # look at the beginning of the sentence to find 1st part of pair
                                    if pairs[j] == pairs[i]:
                                        # marking if correct if first position is marked, too (and vice versa)
                                        corr = (user_array[i][1] == user_array[j][1])
                                        found = True
                                        break
                            if not found:  # first occurence is always wrong if set
                                if user_array[i][1] == '1':
                                    corr = False
                                else:
                                    corr = True
                        else:
                            if user_array[i][1] == '1':
                                corr = False  # marking a MAY comma slot is always false
                            else:
                                corr = True

                    # case 3: mode = 0 (MUST NOT)
                    if rule.mode == 0:
                        corr = user_array[i] in ['00', '11']  # right if not set and not marked (and vice versa)

                    userrule.count(correct=corr)
                    if not corr:
                        SolutionRule(solution=solution, rule=rule, error=True).save()  # save rule to solution
                    if not rule.code.startswith('E'): # count everything but error positions
                        self.count(corr)
                        self.save()
                    if first: # save response info only for first rule (other must be equal)
                        resp.append({'correct': corr, 'rule': {'code': rule.code, 'mode': rule.mode}})
                        first = False

        return resp

    def roulette_wheel_selection(self):
        """
        gets a new sentence via roulette wheel, chooses random among sentences
        :return: a randomly chosen SentenceRule object
        """

        roulette_list = []
        active_rules = 0
        for ur in UserRule.objects.filter(user=self, active=True).all():
            for i in range(2**(4-ur.box)):  # Spaced repetition algorithm: Each box is half probable than previous
                roulette_list.append(ur.rule.code)
            active_rules += 1

        if active_rules >= 4:  # error rules are activated with fourth rule

            for r in Rule.objects.filter(code__startswith='E').all():
                    # all error rules are treated like box 3
                    # TODO: treat error rules like normal rules
                    roulette_list.append(r.code)
                    roulette_list.append(r.code)
        # print(roulette_list)
        index = random.randint(0, len(roulette_list)-1)
        rule_obj = Rule.objects.filter(code=roulette_list[index])
        # print("Select for {}".format(rule_obj))
        # filter out all sentences that have higher rules than current user's progress
        possible_sentences = []
        for sr in SentenceRule.objects.filter(rule=rule_obj[0],sentence__active=True).all():
            ok = True
            for r in sr.sentence.rules.all():
                if r.code in self.rule_order and (self.rule_order.index(r.code) > (self.rules_activated_count-1)):
                    ok = False
                    break
            if ok:
                try:
                    us = UserSentence.objects.get(user=self, sentence=sr.sentence)
                    count = us.count
                except UserSentence.MultipleObjectsReturned:
                    count = 0
                except UserSentence.DoesNotExist:
                    count = 0
                possible_sentences.append([sr,count])  # collect sentence and per user counter for the sentence

        if len(possible_sentences) == 0: # HACK: No sentence? Try again # TODO: find a real solution
            return self.roulette_wheel_selection()

        possible_sentences.sort(key=lambda sentence:sentence[1])  # sort ascending by counts

        if possible_sentences[0][1] == 0:  # first use all sentences at least once
            num = 1                        # i.e. if least used sentence has zero count, use it
        else:
            num = min(3,len(possible_sentences))  # else choose from three least often used

        return random.choice(possible_sentences[:num])[0]  # randomly choose and return SentenceRule object


    def may_roulette_wheel_selection(self):
        """
        gets a new may sentence via roulette wheel, chooses random among sentences
        :return: roulette_list with accumulated rules
        """
        may_obj = Rule.objects.filter(mode=1)
        dict = self.get_dictionary()
        may_roulette_list = []
        sum = 0

        for rule in range(len(may_obj) - 1):
            a, b = re.split(r'/', dict[str(may_obj[rule])])
            sum += int(b)

        for rule in range(len(may_obj) - 1):
            a, b = re.split(r'/', dict[str(may_obj[rule])])
            if int(b) != 0:
                ratio = int((int(a) / sum) * 100)
            else:
                ratio = 1
            for i in range(ratio):
                may_roulette_list.append(may_obj[rule])

        rule_index = random.randint(0, len(may_roulette_list) - 1)
        sent_obj = SentenceRule.objects.filter(rule=may_roulette_list[rule_index])
        sent_index = random.randint(0, len(sent_obj) - 1)

        return sent_obj[sent_index].sentence

    def sentence_selector(self):
        may_obj = Rule.objects.filter(mode=1)
        rule_index = random.randint(0, len(may_obj) - 1)
        sent_obj = SentenceRule.objects.filter(rule=may_obj[rule_index])
        sent_index = random.randint(0, len(sent_obj) - 1)
        return may_obj

    def explicit_data_study(self):
        return User.abschluss.get(self.data_study,"ungültig")

    def explicit_data_semester(self):
        sems = {
            0: "nicht angegeben",
            1: "1./2.",
            2: "3./4.",
            3: "5./6.",
            4: "7./8.",
            5: "9./10.",
            6: "höher"
        }
        return sems.get(self.data_semester, "ungültig")

    def explicit_subject(self, s):
        subs = {
            10: "Anglistik/Englisch",
            11: "Betriebswirtschaftslehre",
            12: "Biologie",
            13: "Chemie",
            14: "Cognitive Science",
            15: "Erziehungswissenschaft",
            16: "Evangelische Theologie",
            17: "Französisch",
            18: "Geographie/Erdkunde",
            19: "Germanistik/Deutsch",
            20: "Geschichte",
            21: "Informatik",
            22: "Islamische Theologie",
            23: "Katholische Theologie",
            24: "Kunst/Kunstpädagogik",
            25: "Latein",
            26: "Literatur und Kultur in Europa",
            27: "Mathematik",
            28: "Musik",
            29: "Physik",
            30: "Psychologie",
            31: "Rechtswissenschaft",
            32: "Romanistik",
            33: "Sachunterricht",
            34: "Sport/Sportwissenschaft",
            35: "Sprache in Europa",
            36: "Textiles Gestalten",
            37: "Sonstiges Fach",
        }
        return subs.get(s, "ungültig")

    def explicit_data_subject1(self):
        return self.explicit_subject(self.data_subject1)

    def explicit_data_subject2(self):
        return self.explicit_subject(self.data_subject2)

    def explicit_data_subject3(self):
        return self.explicit_subject(self.data_subject3)

    def explicit_data_study_permission(self):
        perms = {
            0: "nicht angegeben",
            1: "Abitur (oder äquivalent)",
            2: "Fachabitur (oder äquivalent)",
            3: "Berufsqualifikation",
            4: "sonstige",
            5: "nicht studierend",
        }
        return perms.get(self.data_study_permission, "ungültig")

    def tries(self):
        return Solution.objects.filter(user=self).count()

    def errors(self):
        return SolutionRule.objects.filter(solution__user=self).count()

    def total_time(self):
        te = Solution.objects.filter(user=self).aggregate(models.Sum('time_elapsed'))['time_elapsed__sum']
        return te or 0

    def total_time_formatted(self):
        tt = self.total_time()
        minutes = int(tt/60000)
        seconds = int(tt/1000) - minutes*60
        return "{:3d}:{:02d}".format(minutes, seconds)

class UserRule(models.Model):

    """
    Intermediate model for ManyToMany-Relationship of Users and Rules.

    box - 0-based index of box for spaced repetition (0 = most often, 4 = least often)
    
    Position indicates the 0-based position in the sentence.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    box = models.IntegerField(default=0)  # in which spaced repetition box (0-4) does the rule sit?
    score = models.FloatField(default=0.0)  # score counter for advancing/degrading rule to boxes
    total = models.IntegerField(default=0)  # total rule solution counter
    correct = models.IntegerField(default=0)  # correct rule solution counter

    def count(self, correct=True, tries=1):
        """Register solution for a rule.
        
        correct: Was the rule applied correctly?
        try: How many tries did the user need? (1,2,3,...)"""

        # print("Count {} for {}".format(correct, self.rule))

        self.total += 1  # we had one rule application

        # score is used to determine when a rule shall be placed in another box
        # it differs from trad. spaced repetition because not a single sentence
        # is repeated but a rule (that occurs in many diff. sentences)
        # so we don't upgrade/downgrade immediately
        # upgrade to higher box: score > 3 (3 or more correct applications in a row (% numtries))
        # downgrade to box 0: score <= -3 (3 or more incorrect applications in a row)
        #
        if self.score >=0: # we're in a positive run
            if correct:
                self.score += 1/tries  # it's worth 1/numtries
            else:
                self.score = -1
        else:
            if correct:
                self.score = 1/tries
            else:
                self.score -= 1

        if correct:
            self.correct += 1
        if self.score <= -4:
            self.box = 0  # return to first box on error (leitner algorithm)
            self.score = 0
        elif self.score >= 3 and self.box < 4:  # three correct tries: advance a box (up to box 4)
            self.box += 1
            self.score = 0
        self.save()

    def __str__(self):
        return "{} / {}: Box {}, Score {}, {}/{} correct".format(self.user.user_id, self.rule.code, self.box, self.score, self.correct, self.total)


class UserSentence(models.Model):

    """
    Intermediate model for ManyToMany-Relationship of Users and Sentences.

    Counter indicates how many times the user has seen the sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='link_to_user')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.IntegerField()

    def __str__(self):
        return "{}:{}:{}".format(self.user.id, self.sentence.text, self.count)

    class Meta:
        ordering = ('count',)


class Solution(models.Model):
    """
    Represents one solutions to a sentence.
    Solutions are stored as bitfields for a sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=64)  # TODO: make it an enum
    solution = models.CharField(max_length=255)
    time_elapsed = models.IntegerField(default=0) # time in ms
    mkdate = models.DateTimeField(auto_now_add=True)
    rules = models.ManyToManyField(Rule, through='SolutionRule')

    def __str__(self):
        return "User {} for Sentence {} - {} ms".format(self.user.id, self.sentence.id, self.time_elapsed)


class SolutionRule(models.Model):
    """
    Represents error in solutions for direct access to mistaken rules.
    """

    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    error = models.BooleanField(default=True)

    def __str__(self):
        return "User {} for Rule {} in Sentence {} - Error: {}".format(
            self.solution.user.id,
            self.rule.code,
            self.solution.sentence.id,
            self.error
        )