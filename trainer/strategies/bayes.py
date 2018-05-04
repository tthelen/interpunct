from trainer.models import User, Rule, UserRule, SentenceRule, UserSentence, models
import numpy as np
from itertools import repeat
import random


class StaticNet:
    """
    represents the user specific static model containing all rules to be taught
    """

    def __init__(self):
        """
        creates the static network containing all rules
        initial state contains the probabilities from MT Huber
        :return:
        """

        self.rules = {
            # dict storing rule code as key and knowledge percentage as value
            "A1": 69.631,
            "A2": 74.6235,
            "A3": 97.592,
            "A4": 76.809,
            "B1.1": 66.6675,
            "B1.2": 95.471,
            "B1.3": 79.8385,
            "B1.4.1": 69.2485,
            "B1.4.2": 71.708,
            "B1.5": 85.081,
            "B2.1": 68.159,
            "B2.2": 68.159,
            "B2.3": 68.159,
            "B2.4.1": 87.7055,
            "B2.4.2": 87.7055,
            "B2.5": 96.038,
            "C1": 72.46,
            "C2": 67.0795,
            "C3.1": 81.5305,
            "C3.2": 81.5305,
            "C4.1": 68.455,
            "C5": 69.389,
            "C6.1": 87.4245,
            "C6.2": 84.33,
            "C6.3.1": 81.628,
            "C6.3.2": 68.568,
            "C6.4": 81.628,
            "C7": 77.7395,
            "C8": 81.5305,
            "D1": 75.5315,
            "D2": 70.018,
        }
        self.paragraphs = {  # the overall knowledge of a rule is computed by the sub rules it depends on
            "71": (self.rules["A1"][4]),
            "72": (self.rules["A2"][4] * self.rules["A4"][4]),
            "73": (self.rules["A3"][4]),
            "74": (self.rules["B1.1"][4] * self.rules["B1.2"][4] * self.rules["B1.3"][4] * self.rules["B1.4.1"][4] *
                   self.rules["B1.4.2"][4]),
            "75": (self.rules["B2.1"][4] * self.rules["B2.2"][4] * self.rules["B2.3"][4] * self.rules["B2.4.1"][4] *
                   self.rules["B.2.4.2"][4] * self.rules["B2.5"][4]),
            "76": (self.rules["B1.5"][4]),
            "77": (self.rules["C1"][4] * self.rules["C2"][4] * self.rules["C3.1"][4] * self.rules["C3.2"][4] *
                   self.rules["C4.1"][4] * self.rules["C5"][4] * self.rules["C6.1"][4] * self.rules["C6.3.1"][4] *
                   self.rules["C7"][4] * self.rules["C8"][4]),
            "78": (self.rules["C6.2"][4] * self.rules["C6.4"][4] * self.rules["C6.3.1"][4]),
            "79": (self.rules["D1"][4] * self.rules["D2"][4])
        }

        self.sections = {
            "Aufzaehlung": (self.paragraphs["71"] * self.paragraphs["72"] * self.paragraphs["73"]),
            "Zusaetze": (self.paragraphs["74"] * self.paragraphs["75"] * self.paragraphs["76"]),
            "Teilsaetze": (self.paragraphs["77"] * self.paragraphs["78"] * self.paragraphs["79"])
        }
        self.overall = (self.sections["Aufzaehlung"] * self.sections["Zusaetze"] * self.sections["Teilsaetze"])


class DynamicNet(models.Model):

    def __init__(self, strategy, user):
        """Initialize DynamicNet as list of DynamicNodes.
        :param strategy BayesianStrategy object - for parameter access
        :param user User Object
        """
        self.strategy = strategy
        self.user = user
        self.Net = list()
        self.current = None
        for i in UserRule.objects.filter(user=self.user, dynamicnet_active=True):
            node = DynamicNode(self.strategy, user, i.rule.code)
            if i.dynamicnet_current:
                self.current = node
            self.Net.append(node)

    def count_known(self):
        "Count known Rules"
        cnt = 0
        for i in self.Net:
            if i.known():
                cnt+=1
        return cnt


class DynamicNode:
    """
    represents a node in the dynamic net
    A node consists of
        array (3x?) (one rowfor each task one), storing the results from the last few answers (just booleans)
        array representing the over-all performances per task
        a value representing the over-all (from all tasks) knowledge level
        a count for how often this rule was already trained (no matter the task type)
        and the rule code
    """

    def __init__(self, strategy, user, ruleCode):
        """Initialize a dynamic node.
        :param strategy BayesianStrategy object for parameter access
        :param user User object
        :param ruleCode rule.code for the rule represented by this node
        """

        # data model:
        # dynamicnet_active = models.BooleanField(
        #    default=False)  # is rule part of user's current dynamic net? (see strategies/bayes.py)
        # dynamicnet_count = models.IntegerField(default=0)  # how often has rule been
        # dynamicnet_current = models.BooleanField(default=False)  # is rule current (=main focus) rule?
        # dynamicnet_history1 = models.IntegerField(default=0)  # Bitfield for history of task type 1 (COMMA_SET)
        # dynamicnet_history2 = models.IntegerField(default=0)  # Bitfield for history of task type 2 (COMMA_CORRECT)
        # dynamicnet_history3 = models.IntegerField(default=0)  # Bitfield for history of task type 1 (COMMA_EXPLAIN)
        # access with: self.ur.dynamicnet_active...
        # after setting, don't forget self.ur.save()

        self.strategy = strategy # a BayesianStrategy object for parameter access
        self.ur = UserRule.objects.get(user=user, rule__code=ruleCode)
        self.ruleCode = ruleCode
        self.value = 0.0
        if self.ur.dynamicnet_active:
            # calculate value
            self.value = self.get_value()
        else: # activate this rule in user's dynamic net
            self.value = self.ur.staticnet
            self.ur.dynamicnet_active = True
            self.ur.save()

    def get_value(self):
        """Calculate value from history"""
        max = self.strategy.necReps  # arraysize
        # true python magic: count bits
        sum1 = bin(self.ur.dynamicnet_history1 % 2 ** (max - 1)).count('1')
        sum2 = bin(self.ur.dynamicnet_history2 % 2 ** (max - 1)).count('1')
        sum3 = bin(self.ur.dynamicnet_history3 % 2 ** (max - 1)).count('1')
        return (sum1/max)*0.2 + (sum2/max)*0.45 + (sum3/max)*0.35

    def known(self):
        """Is the rule known (true) or forgotten (false)"""
        return self.ur.dynamicnet_count >= self.strategy.necReps \
               and self.value >= self.strategy.threshold

    def storeAnswer(self, taskNumber, correct):
        """Update node values after a solution has been submitted"""
        self.ur.dynamicnet_count += 1  # increase count
        if taskNumber == 1:
            # move bits in integer to left and fill new position with 0 (default) or 1 (if correct)
            self.ur.dynamicnet_history1 = self.ur.dynamicnet_history1 << 1
            if correct:
                self.ur.dynamicnet_history1 &= 1
        if taskNumber == 2:
            self.ur.dynamicnet_history2 = self.ur.dynamicnet_history2 << 1
            if correct:
                self.ur.dynamicnet_history2 &= 1
        if taskNumber == 3:
            self.ur.dynamicnet_history3 = self.ur.dynamicnet_history3 << 1
            if correct:
                self.ur.dynamicnet_history3 &= 1

        self.value = self.get_value()
        self.ur.save()

class BayesStrategy:
    "A strategy based on bayesian network for selecting the next task"

    def __init__(self, user, threshold=0.75, necReps=8):
        """
        works as konstruktor, at initializing two models are created.
        model 1 contains all rules (static model)
        model 2 is empty at initial state (dynamic model)
        :param user: user object (from models.py)
        :param threshold: indicates required percentage for rule to be learned
        :param necReps: number of minimum repititons a rule needs to have had
        """

        self.user = user
        self.threshold = threshold
        self.necReps = necReps  # numbers of minimum repititions a rule needs to have been applied to
        #self.staticNet = StaticNet()
        self.dynamicNet = DynamicNet(self, self.user)

        self.start_values = {
            # dict storing rule code as key and knowledge percentage as value
            "A1": 69.631,
            "A2": 74.6235,
            "A3": 97.592,
            "A4": 76.809,
            "B1.1": 66.6675,
            "B1.2": 95.471,
            "B1.3": 79.8385,
            "B1.4.1": 69.2485,
            "B1.4.2": 71.708,
            "B1.5": 85.081,
            "B2.1": 68.159,
            "B2.2": 68.159,
            "B2.3": 68.159,
            "B2.4.1": 87.7055,
            "B2.4.2": 87.7055,
            "B2.5": 96.038,
            "C1": 72.46,
            "C2": 67.0795,
            "C3.1": 81.5305,
            "C3.2": 81.5305,
            "C4.1": 68.455,
            "C5": 69.389,
            "C6.1": 87.4245,
            "C6.2": 84.33,
            "C6.3.1": 81.628,
            "C6.3.2": 68.568,
            "C6.4": 81.628,
            "C7": 77.7395,
            "C8": 81.5305,
            "D1": 75.5315,
            "D2": 70.018,
        }

    def init_rules(self):
        """Initialize active rules for user."""

        # create correct rules
        for r in Rule.objects.all():
            try:
                ur = UserRule(rule=r, user=self.user, active=False,
                              dynamicnet_active=False,
                              staticnet=self.start_values[r.code])
                ur.save()
            except KeyError: # ignore rules without start_value
                pass

        # activate first rule
        new_rule = Rule.objects.get(code="A1")
        ur = UserRule.objects.get(rule=new_rule, user=self.user)
        ur.dynamicnet_current = True
        ur.dynamicnet_active = True
        ur.save()

        self.user.rules_activated_count = 1  # activate first rule for next request
        self.user.save()

    def update(self, rule, taskNumber, correct):
        """
        updates the static model
        should be called if the current focus rule is over threshold
        :param DynamicNet: current dynamic net which shall be used to update static net
        :param StaticNet: network containing all rules, shall be updated with values from Dynamic net
        :return: new updated version of the static net
        """
        node = DynamicNode(self.user, rule.code)
        node.storeAnswer(taskNumber, correct)

    def selectNewRule(self):
        """
        function for selecting the next rule.
        Considers "forgotten" rules (rules below threshold in dynamic net) first
        :param dynamicNet:
        :param staticNet:
        :return: next rule to be presented, True if rule is a reminder, false if it is a new rule
        """
        #assert isinstance(dynamicNet, DynamicNet)
        #assert isinstance(staticNet, StaticNet)
        reminder = None

        # before choosing new rule from static net, check whether a rule was forgotten
        possibleRules = list()
        nextRule = None
        #look for all forgotten rules
        for i in self.dynamicNet.Net:
            assert isinstance(i, DynamicNode)
            if not i.known():
                possibleRules.append(i)
        if possibleRules: # if there are forgotten rules
            nextRule = possibleRules[0]
            assert isinstance(nextRule,DynamicNode)
            for i in possibleRules:
                if i.value < nextRule.value:
                    nextRule = possibleRules[i] # and  choose the one with the worst performance

            if nextRule.ur.dynamicnet_count < self.necReps:  # if the rule was already in the iniial dynamic net, jus show the rule
                # introduce the rule
                reminder = False
                return nextRule.ur.rule, reminder
            else:
                reminder = True
            return nextRule.ur.rule, reminder

        #if all rules in the dynamic net are known choose an appropriate next rule from the dynamic net
        else:
            min = 1
            min_node = None
            for i in UserRule.objects.filter(dynamicnet_active=False):
                node = DynamicNode(i.user, i.rule.code)
                if node.value < min:
                    min = node.value
                    min_node = node
        return nextRule.ur.rule, False

    def get_active_rules(self):
        """Return currently active rules, at most 5."""
        # limit = min(self.user.rules_activated_count, 5)
        # res = UserRule.objects.filter(user=self.user, active=1).order_by('box')[:limit]
        # return res
        return UserRule.objects.filter(user=self.user, dynamicnet_active=True)[:5]

    def progress(self):
        """
        method needs to activate userRule by userRule.active = true
        :param self:
        :return: the new rule and whether the user is finished, and if it was a forgotten rule (3 values)
        """

        # TODO: access dynamic net for self.user
        # three cases:
        # 1. User is finished, return false true false
        # 2. User is not finished but needs a new rule, return new rule and false and if it is a reminder
        # 3. User still needs to practise current rule, return false false false

        self.user.rules_activated_count = self.dynamicNet.count_known()+1
        self.user.save()

        # Is user already finished?
        done = True
        for node in self.dynamicNet.Net:
            if not node.known():
                done = False
                break
        if done:
            return False, True, False  # new rule = false, finished = true

        # check the current rule
        currentRule = self.dynamicNet.current
        assert isinstance(currentRule, DynamicNode)

        # if it is known, find a new rule
        if currentRule.known():
            newRule,forgotten = BayesStrategy.selectNewRule()
            return newRule, False, forgotten
        # otherwise return false
        else:
            return False, False, False

    def roulette_wheel_selection(self):

        # select a rule

        # everything under :
        # 75% 10 times
        # 80% 8 times
        # 85% 6 times
        # 90% 4 times
        # 95% 2 times
        # 100% 1 time

        # TODO: access dynamic net from self.user
        RuleNodes = self.dynamicNet.Net # contains a list of all rule nodes
        assert isinstance(self.dynamicNet, DynamicNet)

        pool = list()
        weakRules = list() #contains all rules under 80%
        #create a pool of rules with different weights, makes it more likely to select weak rules
        for node in RuleNodes:
            assert isinstance(node, DynamicNode)
            assert isinstance(node.value, float)
            if node.value < 0.75:
                pool.extend(repeat(node.ruleCode, 10))
                weakRules.append(node.ruleCode)
            elif node.value < 0.8:
                pool.extend(repeat(node.ruleCode, 8))
                weakRules.append(node.ruleCode)
            elif node.value < 0.85:
                pool.extend(repeat(node.ruleCode, 6))
            elif node.value < 0.9:
                pool.extend(repeat(node.ruleCode, 4))
            elif node.value < 0.95:
                pool.extend(repeat(node.ruleCode, 2))
            elif node.value <= 1:
                pool.extend(repeat(node.ruleCode, 1))

        # add error rules if more than 4 rules
        if len(RuleNodes) >= 4:
            for r in Rule.objects.filter(code__startswith='E').all():
                # all error rules are treated like box 3
                # TODO: treat error rules like normal rules
                pool.extend(r.code)
                pool.extend(r.code)

        random.shuffle(pool)  # shuffle the elements in the list
        index = random.randint(0, len(pool) - 1)  # pick a random number
        rule_obj = Rule.objects.filter(code=pool[index])  # and select a random rule code

        # select a sentence
        possible_sentences = []
        contains = None
        activeRules = list()
        for node in self.dynamicNet.Net:
            activeRules.append(node.ur.rule.code)
        # check all active sentences taht include a position for the selected rule
        for sr in SentenceRule.objects.filter(rule=rule_obj[0], sentence__active=True).all():

            includedRules = sr.sentence.rules.all()  # store all rules included in that sentence
            # check whether the rules included in the sentence are a sublist of all active list
            contains = True
            for node in includedRules:
                if node not in activeRules:
                    contains = False

            if contains:
                us = UserSentence.objects.get(user=self.user, sentence=sr.sentence)
                count = us.count
                possible_sentences.append([sr, count])  # store all possible sentences
                possible_sentences.sort(key=lambda sentence: sentence[1])  # sort ascending by counts

        if len(possible_sentences) == 0:  # HACK: No sentence? Try again # TODO: find a real solution
            print("HACK! Try another sentence...")
            return self.roulette_wheel_selection()

        # pick least often used of the possible sentences
        possible_sentences.sort(key=lambda sentence: sentence[1])  # sort ascending by counts
        # are there possible sentences containing a weak rule?
        priorSentence = list()
        for node in possible_sentences:
            assert isinstance(node, SentenceRule)
            #todo how do I iterate over a foreign key
            rulesOfSentence = SentenceRule.objects.filter(sentence=node.sentence)
            if rulesOfSentence.count() > 2: #if sentence contains more than two rules
                union = list(set().union(rulesOfSentence, weakRules))
                if len(union) > 1: #if there is a greater union than 1, copy directly
                    priorSentence.append(node)
                else:
                    assert isinstance(union[0], Rule) #otherwise check that the union is not the selected rule
                    #(union[0].code == rule_obj would happen, if the current selected rule is a weak one
                    if union[0].code != rule_obj: #in this case we rule_obj is not a weak one and we have only one match
                        #with a weak rule
                        priorSentence.append(node)

        sentence = None
        if possible_sentences[0][1] == 0:  # first use all sentences at least once
            num = 1
            sentence = random.choice(possible_sentences[:num])[0]  # i.e. if least used sentence has zero count, use it
        # otherwise choose a sentence which contains a weak rules
        elif len(priorSentence) == 1:
            sentence = priorSentence[0]
        elif len(priorSentence) > 1:
            ran =  random.randint(0, len(priorSentence) - 1)
            sentence = priorSentence[ran]
        else:
            num = min(3, len(possible_sentences)) #otherwise return one sentence which is used less than 3 times
            sentence = random.choice(possible_sentences[:num])[0]

        return sentence

    def update_rank(self, staticModel):
        """
        :param staticModel:
        :return: rank (0-3) of user
        """
        assert (isinstance(staticModel, StaticNet))
        overall = staticModel.overall
        auf = staticModel.sections['Aufzaehlung'] > self.threshold
        teil = staticModel.sections['Teilsaetze'] > self.threshold
        zus = staticModel.sections['Zusaetze'] > self.threshold
        twoComplete = (auf & teil)|(teil & zus) |(auf & zus)
        oneComplete = auf|teil|zus


        #Kommakoenig if above threshold
        if overall > self.threshold:
            return 3
        #Kommakommandant if 10% under threshold or 2 sections over threshold
        if (overall > (self.threshold*0,9) | twoComplete):
            return 2
        # Kommakoener if 0,8 percent uner threshold or one complete section
        if (overall > (self.threshold*0,8) | oneComplete):
            return 1
        # Kommachaot if 0,7 percent uner threshold or one complete section
        else: return 0



