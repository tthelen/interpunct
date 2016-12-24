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
    def __str__(self):
        return self.user_id

    RANKS = (
        (0, 'Kommachaot'),
        (1, 'Kommakönner'),
        (2, "Kommakommandant"),
        (3, 'Kommakönig'),
    )
    user_id = models.CharField(max_length = 255)
    user_rank = models.IntegerField(choices=RANKS, default = 0)
    # counts wrong answers for a specific comma type
    comma_type_false = models.CharField(max_length=400,default="A1:0/0, A2:0/0, A3:0/0, A4:0/0, B1.1:0/0, B1.2:0/0, B1.3:0/0, B1.4.1:0/0, B1.4.2:0/0, B1.5:0/0, B2.1:0/0, B2.2:0/0, B2.3:0/0, B2.4.1:0/0, B2.4.2:0/0, B2.5:0/0, C1:0/0, C2:0/0, C3.1:0/0, C3.2:0/0, C4.1:0/0, C4.2:0/0, C5:0/0, C6.1:0/0, C6.2:0/0, C6.3.1:0/0, C6.3.2:0/0, C6.4:0/0, C7:0/0, C8:0/0, D1:0/0, D2:0/0, D3:0/0, E1:0/0")

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
        if rank_counter == 2*(len(dict)-1):
            self.user_rank = 2
            self.save()
        if rank_counter == 4 * (len(dict) - 1):
            self.user_rank = 3
            self.save()

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

    def count_false_types_task1(self, user_array_str, solution_array):
        """
        count false types for: AllKommaSetzen
        :param user_array: contains submitted array of bools
        :param solution_array: contains comma types
        """
        dict = self.get_dictionary()
        user_array = re.split(r'[ ,]+', user_array_str)
        # current_rule_list = []
        for i in range(len(solution_array) - 2):
            if len(solution_array[i]) == 0 and int(user_array[i]) == 1:
                a, b = re.split(r'/', dict["E1"])
                dict["E1"] = str(int(a) + 1) + "/" + str(int(b) + 1)
            elif len(solution_array[i]) != 0:
                a, b = re.split(r'/', dict[solution_array[i][0]])
                rule = Rule.objects.get(code=solution_array[i][0])
                if rule.mode == 0 and user_array[i] != "0":  # must not, false
                    dict[solution_array[i][0]] = str(int(a) + 1) + "/" + str(int(b) + 1)
                if rule.mode == 0 and user_array[i] == "0":  # must not, correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 1:  # may, always correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 2 and user_array[i] == "1":  # must, correct
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                if rule.mode == 2 and user_array[i] == "0":  # must, false
                    dict[solution_array[i][0]] = str(int(a) + 1) + "/" + str(int(b) + 1)
                    # current_rule_list.append(rule)
        self.save_dictionary(dict)

    def count_false_types_task2(self, user_array_str, solution_array):
        """
        count false types for: AllKommaErlären
        :param user_array: contains submitted array of bools (checkbox answers)
        :param solution_array: contains comma types
        """

        dict = self.get_dictionary()
        user_array = re.split(r'[ ,]+', user_array_str)
        comma_amout = 0;
        for i in range(len(solution_array) - 2):
            if len(solution_array[i]) != 0:
                a, b = re.split(r'/', dict[solution_array[i][0]])
                rule = Rule.objects.get(code=solution_array[i][0])
                if user_array[comma_amout] == "1":
                    dict[solution_array[i][0]] = str(int(a)) + "/" + str(int(b) + 1)
                elif user_array[comma_amout] == "0":
                    dict[solution_array[i][0]] = str(int(a) + 1) + "/" + str(int(b) + 1)
                comma_amout += 1
        self.save_dictionary(dict)

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

    def naive_task_selection(self):
        """
        Gets a sentence for a rule with the highest false values, chooses random among those sentences
        (pick lowest score rule)
        :return:
        """
        sentence_for_rule = []
        my_dict = self.get_dictionary()
        my_max = 0
        lowest_rule = ""
        for key in my_dict:
            if key != "E1":
                a, b = re.split(r'/', my_dict[key])
                if int(b) == 0:
                    rule_obj = Rule.objects.filter(code = key)
                    count = SentenceRule.objects.filter(rule = rule_obj[0])
                    index = int(random.random() * len(count))
                    return SentenceRule.objects.filter(rule = rule_obj[0])[index].sentence

                elif int(b) != 0 :
                    ratio = (int(b) - int(a))
                    if my_max < ratio:
                        my_max = ratio
                        lowest_rule = key
                    rule_obj = Rule.objects.filter(code=lowest_rule)
                    sentence_for_rule.append(SentenceRule.objects.filter(rule = rule_obj))
                    index = int(random.random() * len(sentence_for_rule))

                    return sentence_for_rule[0][index]


    def roulette_wheel_selection(self):
        """
        gets a new sentence via roulette wheel, chooses random among sentences
        :return: roulette_list with accumulated rules
        """
        dict = self.get_dictionary()
        roulette_list = []
        sum = 0
        for key in dict:
            a, b = re.split(r'/', dict[key])
            sum += int(b)
        for key in dict:
            if key != "E1":
                a, b = re.split(r'/', dict[key])
                if int(b) != 0:
                    ratio = int((int(a)/sum)*100)
                else:
                    ratio = 1
                for i in range(ratio):
                    roulette_list.append(key)
        index = random.randint(0, len(roulette_list)-1)
        rule_obj = Rule.objects.filter(code=roulette_list[index])
        sentence_rule_obj_arr = SentenceRule.objects.filter(rule=rule_obj[0])
        index = int(random.random() * len(sentence_rule_obj_arr))
        return sentence_rule_obj_arr[index].sentence

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