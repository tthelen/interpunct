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
    comma_select: int list of how often comma was set here
    total_submits: number of tries for sentence
    rules: n:m relation to Rule through SentenceRule table (adding position)

    IMPORTANT: The list of words of a sentence must never change!
               Solutions store a bool value for each gap, so gap
               positions must stay fixed.

    Example: Wir essen, Opa.
    """
    text = models.CharField(max_length=2048)
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
        :param boolean_str: string of seleced commas
        """
        selects = self.get_commaselectlist();
        user_select_arr = re.split(r'[,]+', user_select_str)
        for i in range(len(self.get_commalist())):
            if i != len(self.get_commalist())-1:
                selects[i] = str(int(selects[i]) + int(user_select_arr[i])) + ","
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

        for pos in range(len(self.get_words())-1):
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
        rule_list = Rule.objects.all()

        rule_decoded_list = []
        for rule in rule_list:
            rule_decoded_list.append(rule.decode())
        rule_decoded_list.remove(decode_list)

        # Initial Indexing, current commatype
        index_list = [0, 1, 2, 3]
        index = random.choice(index_list)
        index_list.remove(index)

        solution = [0, 0, 0, 0]
        count = Rule.objects.all().count()

        # Random Explanations
        if rank == 0:
            for i in range(4):
                if i != index:
                    tmp = rule_decoded_list[int(random.random() * len(rule_decoded_list))]
                    solution[i] = Rule.objects.get(code=rule_obj.encode(tmp)).description
                    rule_decoded_list.remove(tmp)
                else:
                    solution[i] = rule_obj.description
            return solution, index

        if rank == 1:
            options_1 = self.optionfinder_1(commatype, decode_list, rule_decoded_list)

            # Indexing
            index_1 = random.choice(index_list)
            index_list.remove(index_1)
            # Picking
            if len(options_1) != 0:
                pick = random.randint(0, len(options_1) - 1)
                options_1.remove(options_1[pick])
            else:
                pick = random.randint(0, len(rule_decoded_list) - 1)
                rule_decoded_list.remove(rule_decoded_list[pick])

            # Solution
            for i in range(4):
                if i == index:
                    solution[i] = Rule.objects.get(code=commatype).description
                elif i == index_1 and len(options_1) != 0:
                    solution[i] = Rule.objects.get(code=rule_obj.encode(options_1[pick])).description
                else:
                    solution[i] = Rule.objects.get(code=rule_obj.encode(rule_decoded_list[0])).description
            return solution, index

        if rank == 2:
            options_1 = self.optionfinder_1(commatype, decode_list, rule_decoded_list)
            options_2 = self.optionfinder_2(commatype, decode_list, rule_decoded_list)

            # Indexing for 2 options
            index_2a = random.choice(index_list)
            index_list.remove(index_2a)
            index_2b = random.choice(index_list)
            index_list.remove(index_2b)

            # Solution
            for i in range(4):
                if i == index:
                    solution[i] = Rule.objects.get(code=commatype).description
                elif i == index_2a or i == index_2b:
                    if len(options_2) != 0:
                        pick_2 = random.randint(0, len(options_2) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(options_2[pick_2])).description
                        options_2.remove(options_2[pick_2])
                    elif len(options_1) != 0:
                        pick_2 = random.randint(0, len(options_1) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(options_1[pick_2])).description
                        options_1.remove(options_1[pick_2])
                    else:
                        pick_2 = random.randint(0, len(rule_decoded_list) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(rule_decoded_list[pick_2])).description
                        rule_decoded_list.remove(rule_decoded_list[pick_2])
                else:
                    pick_2 = random.randint(0, len(rule_decoded_list) - 1)
                    solution[i] = Rule.objects.get(code=rule_obj.encode(rule_decoded_list[pick_2])).description
                    rule_decoded_list.remove(rule_decoded_list[pick_2])
            return solution, index

        elif rank == 3:
            options_1 = self.optionfinder_1(commatype, decode_list, rule_decoded_list)
            options_2 = self.optionfinder_2(commatype, decode_list, rule_decoded_list)
            options_3 = self.optionfinder_3(commatype, decode_list, rule_decoded_list)

            # Indexing

            index_3a = random.choice(index_list)
            index_list.remove(index_3a)
            index_3b = random.choice(index_list)
            index_list.remove(index_3b)
            index_3c = random.choice(index_list)
            index_list.remove(index_3c)

            # Solution
            for i in range(4):
                if i == index:
                    solution[i] = Rule.objects.get(code=commatype).description

                elif i == index_3a or i == index_3b or i == index_3c:
                    if len(options_3) != 0:
                        pick_3 = random.randint(0, len(options_3) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(options_3[pick_3])).description
                        options_3.remove(options_3[pick_3])
                    elif len(options_2) != 0:
                        pick_3 = random.randint(0, len(options_2) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(options_2[pick_3])).description
                        options_2.remove(options_2[pick_3])
                    elif len(options_1) != 0:
                        pick_3 = random.randint(0, len(options_1) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(options_1[pick_3])).description
                        options_1.remove(options_1[pick_3])
                    else:
                        pick_3 = random.randint(0, len(rule_decoded_list) - 1)
                        solution[i] = Rule.objects.get(code=rule_obj.encode(rule_decoded_list[pick_3])).description
                        rule_decoded_list.remove(rule_decoded_list[pick_3])
                else:
                    pick_3 = random.randint(0, len(rule_decoded_list) - 1)
                    solution[i] = Rule.objects.get(code=rule_obj.encode(rule_decoded_list[pick_3])).description
                    rule_decoded_list.remove(rule_decoded_list[pick_3])

        return solution, index

    def optionfinder_1(self, commatype, decode_list, rule_decoded_list):
        # Distance 1 e.g. index = A123 ; option.obj = A421
        options_1 = []
        for i in decode_list:
            for j in range(len(rule_decoded_list) - 1):
                if rule_decoded_list[j][0] == i:
                    options_1.append(rule_decoded_list[j])
        return options_1

    def optionfinder_2(self, commatype, decode_list, rule_decoded_list):
        # Distance 2 eg. index A123 ; option.obj = A140
        options_2 = []
        for i in decode_list:
            for j in range(len(rule_decoded_list) - 1):
                if rule_decoded_list[j][0] == i and rule_decoded_list[j][1] == i:
                    options_2.append(rule_decoded_list[j])
        return options_2

    def optionfinder_3(self, commatype, decode_list, rule_decoded_list):
        # Distance 2 eg. index A123 ; option.obj = A140
        options_3 = []
        for i in decode_list:
            for j in range(len(rule_decoded_list) - 1):
                if rule_decoded_list[j][0] == i and rule_decoded_list[j][1] == i and rule_decoded_list[j][2]:
                    options_3.append(rule_decoded_list[j])
        return options_3


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



class User(models.Model):
    def __str__(self):
        return self.user_id

    RANKS = (
        (0, 'Kommachaot'),
        (1, 'Kommakönner'),
        (2, "Kommakommandant"),
        (3, 'Kommakönig'),
    )
    user_id = models.CharField(max_length = 255)
    data = models.CharField(max_length=255, default='')
    user_rank = models.IntegerField(choices=RANKS, default = 0)
    # counts wrong answers for a specific comma type
    comma_type_false = models.CharField(max_length=400,default="A1:0/0, A2:0/0, A3:0/0, A4:0/0, B1.1:0/0, B1.2:0/0, B1.3:0/0, B1.4.1:0/0, B1.4.2:0/0, B1.5:0/0, B2.1:0/0, B2.2:0/0, B2.3:0/0, B2.4.1:0/0, B2.4.2:0/0, B2.5:0/0, C1:0/0, C2:0/0, C3.1:0/0, C3.2:0/0, C4.1:0/0, C4.2:0/0, C5:0/0, C6.1:0/0, C6.2:0/0, C6.3.1:0/0, C6.3.2:0/0, C6.4:0/0, C7:0/0, C8:0/0, D1:0/0, D2:0/0, D3:0/0, E1:0/0")

    # rules_activated: user progress in terms of available rules.
    # Starts at 0, continues to ~40
    rules_activated_count = models.IntegerField(default=0)
    rules = models.ManyToManyField(Rule, through='UserRule')

    rule_order = [
        "A1", # GLEICHRANG
        "A2", # ENTGEGEN
        "B1.1", # NEBEN
        "B2.1", # UMOHNESTATT
        "C1", # PARANTHESE
        "C2", # APPOSITION
        "D1", # ANREDE
        "D2", # AUSRUF
        "A3",
        "A4",
        "B1.2",
        "B1.3",
        "B1.4.1",
        "B1.4.2",
        "B1.5",
        "B2.2",
        "B2.3",
        "B2.4.1",
        "B2.4.2",
        "B2.5",
        "C3.1",
        "C3.2",
        "C4.1",
        "C4.2",
        "C5",
        "C6.1",
        "C6.2",
        "C6.3.1",
        "C6.3.2",
        "C6.4",
        "C7",
        "C8",
        "D3"
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

        # activate first rule
        new_rule = Rule.objects.get(code=self.rule_order[0])
        ur = UserRule.objects.get(rule=new_rule, user=self)
        ur.active = True
        ur.save()

        self.rules_activated_count = 1  # activate first rule for next request
        self.save()

        return new_rule

    def progress(self):
        """Advance to next level, if appropriate.
        
        Returns False is no level progress, the newly activated Rule object otherwise.
        """

        # highest level reached?
        if self.rules_activated_count == len(self.rule_order):
            return False

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
            return new_rule

        return False

    def level_display(self):
        """Return UserRule data for displaying level."""

        res = []
        for i in range(self.rules_activated_count):
            res.append(UserRule.objects.get(user=self, rule=Rule.objects.get(code=self.rule_order[i])))
        return res


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

    def count_false_types_task1(self, user_array_str, solution_array):
        """
        count false types for: AllKommaSetzen
        :param user_array: contains submitted array of bools
        :param solution_array: contains comma types
        """
        user_array = re.split(r'[ ,]+', user_array_str)
        for i in range(len(solution_array) - 1):
            if len(solution_array[i]) == 0 and int(user_array[i]) == 1: # comma in the wild
                userrule = UserRule.objects.get(user=self, rule=Rule.objects.get(code="E1"))
                userrule.count(correct=False)
            elif len(solution_array[i]) != 0: # comma at rule position
                # TODO handle multiple comma types per comma
                rule = Rule.objects.get(code=solution_array[i][0])
                userrule = UserRule.objects.get(user=self, rule=rule)
                if (rule.mode == 0 and user_array[i] == "0") or  \
                   (rule.mode == 1) or \
                   (rule.mode == 2 and user_array[i] == "1"):
                    corr = True
                else:
                    corr = False
                userrule.count(correct=corr)

    def count_false_types_task_correct_commas(self, user_array_str, comma_array_str, solution_array):
        """
        count false types for: AllKommaSetzen
        :param user_array: contains submitted array of bools (positions marked as incorrect)
        :param solution_array: contains comma types
        """
        user_array = re.split(r'[ ,]+', user_array_str)
        comma_array = re.split(r'[ ,]+', comma_array_str)

        for i in range(len(solution_array) - 1):

            if len(solution_array[i]) == 0 and int(comma_array[i]) == 1: # comma in the wild

                if user_array[i]==1:  # wrong comma without rule detected correctly
                    pass
                else:  # wrong comma without rule not detected correctly
                    userrule = UserRule.objects.get(user=self, rule=Rule.objects.get(code="E1"))
                    userrule.count(correct=False)

            elif len(solution_array[i]) != 0: # rule position

                # TODO handle multiple comma types per comma
                rule = Rule.objects.get(code=solution_array[i][0])
                userrule = UserRule.objects.get(user=self, rule=rule)

                # case 1: mode = 2 (MUST)
                if rule.mode == 2:
                   corr = (user_array[i] != comma_array[i])  # right if set and not marked (and vice versa)

                # case 2: mode = 1 (MAY)
                if rule.mode == 1:
                   corr = not user_array[i]  # marking a MAY comma slot is always false

                # case 3: mode = 0 (MUST NOT)
                if rule.mode == 0:
                    corr = (user_array[i] == comma_array[i])  # right if not set and not marked (and vice versa)

                userrule.count(correct=corr)

    def count_false_types_task_explain_commas(self, user_array, solution_array):
        """
        count false types for: AllKommaErlären
        :param user_array: contains submitted array of bools (checkbox answers)
        :param solution_array: contains comma types
        """

        comma_amout = 0;
        for i in range(len(solution_array) - 1):
            if len(solution_array[i]) != 0:
                rule = Rule.objects.get(code=solution_array[i][0])
                ur = UserRule.objects.get(user=self, rule=rule)
                if user_array[comma_amout] == "1":
                    ur.count(correct=True)
                elif user_array[comma_amout] == "0":
                    ur.count(correct=False)
                comma_amout += 1

    def count_false_types_task3(self, user_array_str, solution_array):
        """
        count false types for: KannKommaLöschen
        :param user_array_str:
        :param solution_array:
        """
        dict = self.get_dictionary()
        user_array = re.split(r'[ ,]+', user_array_str)
        for i in range(len(solution_array) - 2):
            if len(solution_array[i])!=0:
                a, b = re.split(r'/', dict[solution_array[i][0]])
                rule = Rule.objects.get(code=solution_array[i][0])
                if rule.mode == 1 and user_array[i] == "0":
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                elif rule.mode == 1 and user_array[i] == "1":
                    dict[solution_array[i][0]] = str(int(a) + 1) + "/" + str(int(b) + 1)
                elif rule.mode == 2 and user_array[i] == "0":
                    dict[solution_array[i][0]] = str(int(a) + 1) + "/" + str(int(b) + 1)
        self.save_dictionary(dict)

    def count_false_types_task4(self, user_array_str, solution_array):
        """
        count false types for: KannKommaSetzen
        :param user_array_str:
        :param solution_array:
        """
        dict = self.get_dictionary()
        user_array = re.split(r'[ ,]+', user_array_str)
        for i in range(len(solution_array) - 2):
                a, b = re.split(r'/', dict[solution_array[i][0]])
                rule = Rule.objects.get(code=solution_array[i][0])
                if rule.mode == 1 and user_array[i] == "0":
                    dict[solution_array[i][0]] = str(int(a)+1)   + "/" + str(int(b) + 1)
                elif rule.mode == 1 and user_array[i] == "1":
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                elif rule.mode == 0 and user_array[i] == "1":
                    dict[solution_array[i][0]] = str(int(a)+1) + "/" + str(int(b) + 1)
        self.save_dictionary(dict)

    def roulette_wheel_selection(self):
        """
        gets a new sentence via roulette wheel, chooses random among sentences
        :return: roulette_list with accumulated rules
        """

        roulette_list = []
        for ur in UserRule.objects.filter(user=self, active=True).all():
            for i in range(2**(4-ur.box)):  # Spaced repetition algorithm: Each box is 5 times less probable then previous
                roulette_list.append(ur.rule.code)

        index = random.randint(0, len(roulette_list)-1)
        rule_obj = Rule.objects.filter(code=roulette_list[index])

        # filter out all sentences that have higher rules than current user's progress
        possible_sentences = []
        for sr in SentenceRule.objects.filter(rule=rule_obj[0]).all():
            ok = True
            for r in sr.sentence.rules.all():
                if self.rule_order.index(r.code) > (self.rules_activated_count-1):
                    ok = False
                    break
            if ok:
                possible_sentences.append(sr.sentence)

        return random.choice(possible_sentences)

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
        if self.score <= -3:
            self.box = 0  # return to first box on error (leitner algorithm)
            self.score = 0
        elif self.score > 3 and self.box < 4:  # three correct tries: advance a box (up to box 4)
            self.box += 1
            self.score = 0
        self.save()

    def __str__(self):
        return "{} / {}: Box {}, Score {}, {}/{} correct" % (
            self.user.user_id, self.rule.code,
            self.box, self.score, self.correct, self.total)


class Solution(models.Model):
    """
    Represents one solutions to a sentence.
    Solutions are stored as bitfields for a sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=64)  # TODO: make it an enum
    solution = models.CharField(max_length=255)
    mkdate = models.DateTimeField(auto_now_add=True)
