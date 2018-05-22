from trainer.models import User, Rule, UserRule, SentenceRule, UserSentence, models, UserPretest

from itertools import repeat, chain
import random

class StaticNet:
    def __init__(self, dynamicNet):
        """
        static net which represent the knowledge state of the user across the 3 sections
        :param dynamicNet: the "working net" which gives the learning results
        """
        self.dynamicNet = dynamicNet
        self.auf = ["A1","A2","A4","A3"]
        self.teil = ["B1.1","B1.2","B1.3","B1.4.1","B1.4.2","B2.1","B2.2","B2.3","B2.4.1","B.2.4.2","B2.5","B1.5"]
        self.zus = ["C1","C2","C3.1","C3.2","C4.1","C5","C6.1","C6.3.1","C7","C8","C6.2","C6.4","C6.3.1","D1","D3"]
        self.aufValue = 1
        self.teilValue = 1
        self.zusValue = 1

        self.updateStatic(dynamicNet)

    def updateStatic(self, dynamicNet):
        # calculate the values for the skeleton
        countauf = 0
        countteil = 0
        countzus = 0
        for i in self.dynamicNet.Net:
            assert (isinstance(i, DynamicNode))
            # multiply node values according to their parent node
            if i.ruleCode in self.auf:
                self.aufValue *= i.get_value()
                countauf *= 1
            elif i.ruleCode in self.teil:
                self.teilValue *= i.get_value()
                countteil += 1
            elif i.ruleCode in self.zus:
                self.zusValue *= i.get_value()
                countzus += 1
            else:
                raise RuntimeError("No parent node can be assigned")
        # and divide by count to get the average performance
        if countauf != 0:
            self.aufValue /= countauf
        else:
            countauf = 0
        if countteil != 0:
            self.teilValue /= countteil
        else:
            countteil = 0
        if countzus != 0:
            self.zusValue /= countzus
        else:
            self.zusValue = 0
        # get the overall value
        self.overall = (self.aufValue * self.teilValue * self.zusValue)/3


class DynamicNet(models.Model):

    def __init__(self, strategy, user): #activatedByTest
        """Initialize DynamicNet as list of DynamicNodes.
        :param strategy BayesianStrategy object - for parameter access
        :param user User Object
        """
        self.strategy = strategy
        self.user = user
        self.Net = list()
        self.current = None

        self.updateNet()
        #keys = BayesStrategy.start_values.keys()
        #for i in keys:
        #     self.Net.append(DynamicNode(strategy=BayesStrategy,user=self.user,ruleCode=i))
         #for i in activatedByTest:
         #   i.activateNode()

    def updateNet(self):
        for i in UserRule.objects.filter(user=self.user,dynamicnet_active= True): # i is an user rule object
            try:
                node = DynamicNode(self.strategy, self.user, i.rule.code, self)
                if i.dynamicnet_current:
                    self.current = node
            except KeyError:
                pass
            self.Net.append(node)

    def setCurrent(self,rule):
        """
        updates the current rule of the net
        :param rule: rule which should be set as the current rule
        :return:
        """
        self.updateNet()
        self.current.ur.dynamicnet_current = False
        self.current.ur.save()
        print(rule.code)
        for node in self.Net:
            if node.ruleCode == rule.code:
                print("find new current")
                self.current = node
                self.current.ur.dynamicnet_current = True
                print(self.current.ur)
                self.current.ur.save()
                break
        else:
            print("not found")

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

    def __init__(self, strategy, user, ruleCode, dynamicNet):
        """Initialize a dynamic node.
        :param strategy BayesianStrategy object for parameter access
        :param user User object
        :param ruleCode rule.code for the rule represented by this node
        :param dynamicNet the DynamicNet object to which the node belongs
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
        self.value = BayesStrategy.start_values[self.ruleCode]
        self.dynamicNet = dynamicNet
        if self.ur.dynamicnet_active:
            # calculate value
            self.value = self.get_value()
            print("Node value",self.value)
            self.ur.save()
        else: # activate this rule in user's dynamic net
            self.value = BayesStrategy.start_values[self.ruleCode]
            self.ur.save()

    def activateNode(self):
        self.ur.dynamicnet_active = True
        self.ur.save()

    def get_value(self):
        max = 4 #maximum amount of repititions a rule needs
        toconsider = 6 #only the last 6 answers are going to be considered
        sum1 = 0
        sum2 = 0
        sum3 = 0
        total_count = self.ur.total

        # calculating value for node "task 1"
        if self.ur.dynamicnet_count1 < 6:
            if self.ur.dynamicnet_count1 == 0:
                sum1=BayesStrategy.start_values[self.ruleCode]
            else:
                sum1 = bin(self.ur.dynamicnet_history1 % 2 ** (self.ur.dynamicnet_count1)).count('1')/self.ur.dynamicnet_count1 if self.ur.dynamicnet_count1 else BayesStrategy.start_values[self.ruleCode]
        else:
            sum1 = bin(self.ur.dynamicnet_history1 % 2 ** (toconsider)).count('1')/toconsider

        #calculating value for node "task2"
        if self.ur.dynamicnet_count2 < 6:
            if self.ur.dynamicnet_count2 == 0:
                sum2 = BayesStrategy.start_values[self.ruleCode]
            else:
                sum2 = bin(self.ur.dynamicnet_history2 % 2 ** (self.ur.dynamicnet_count2)).count('1')/self.ur.dynamicnet_count2 if self.ur.dynamicnet_count2 else BayesStrategy.start_values[self.ruleCode]
        else:
            sum2 = bin(self.ur.dynamicnet_history2 % 2 ** (toconsider)).count('1')/toconsider

        #if task3 was not shown yet calculate value only by sum1 and sum2
        print (self.ur.dynamicnet_count3, self.ur.rule.code)
        if self.ur.dynamicnet_count3 == 0:
            value = sum1 * 0.4 + sum2 * 0.6
            print(self.ur.rule.code, "value = {} * 0.4 + {} * 0.6 = {}".format(sum1, sum2, value))
            return value

        #calculating value for node "task3"
        if self.ur.dynamicnet_count3 < 6:
            assert(self.ur.dynamicnet_count3 != 0), "This value should not be 0"
            sum3 = bin(self.ur.dynamicnet_history3 % 2 ** (self.ur.dynamicnet_count3)).count('1')/self.ur.dynamicnet_count3 if self.ur.dynamicnet_count3 else BayesStrategy.start_values[self.ruleCode]
        else:
            sum3 = bin(self.ur.dynamicnet_history3 % 2 ** (toconsider)).count('1')/toconsider
        value = sum1 * 0.25 + sum2 * 0.4 + sum3 * 0.35
        print(self.ur.rule.code , "value = {} * 0.25 + {} * 0.4 + {} * 0.35 = {}".format(sum1, sum2, sum3, value))
        return value


    def known(self):
        """Is the rule known (true) or forgotten (false)"""
        known = (self.ur.dynamicnet_count > 4) and (self.get_value() >= 0.75)
        return known

    def storeAnswer(self, taskNumber, correct):
        """Update node values after a solution has been submitted"""
        self.ur.dynamicnet_count += 1  # increase count
        if taskNumber == 1:
        # move bits in integer to left and fill new position with 0 (default) or 1 (if correct)
            self.ur.dynamicnet_history1 = self.ur.dynamicnet_history1 << 1
            self.ur.dynamicnet_count1 += 1
            if correct:
                self.ur.dynamicnet_history1 |= 1
        if taskNumber == 2:
            self.ur.dynamicnet_history2 = self.ur.dynamicnet_history2 << 1
            self.ur.dynamicnet_count2 += 1
            if correct:
                self.ur.dynamicnet_history2 |= 1
        if taskNumber == 3:
            self.ur.dynamicnet_history3 = self.ur.dynamicnet_history3 << 1
            self.ur.dynamicnet_count3 += 1
            if correct:
                self.ur.dynamicnet_history3 |= 1

        self.value = self.get_value()
        self.known = self.known()
        self.ur.save()

class BayesStrategy:
    "A strategy based on bayesian network for selecting the next task"
    start_values = {
        # dict storing rule code as key and knowledge percentage as value
        "A1": 0.69631,
        "A2": 0.746235,
        "A3": 0.97592,
        "A4": 0.76809,
        "B1.1": 0.666675,
        "B1.2": 0.95471,
        "B1.3": 0.798385,
        "B1.4.1": 0.692485,
        "B1.4.2": 0.71708,
        "B1.5": 0.85081,
        "B2.1": 0.68159,
        "B2.2": 0.68159,
        "B2.3": 0.68159,
        "B2.4.1": 0.877055,
        "B2.4.2": 0.877055,
        "B2.5": 0.96038,
        "C1": 0.7246,
        "C2": 0.670795,
        "C3.1": 0.815305,
        "C3.2": 0.815305,
        "C4.1": 0.68455,
        "C5": 0.69389,
        "C6.1": 0.874245,
        "C6.2": 0.8433,
        "C6.3.1": 0.81628,
        "C6.3.2": 0.68568,
        "C6.4": 0.81628,
        "C7": 0.777395,
        "C8": 0.815305,
        "D1": 0.755315,
        "D3": 0.70018,
        "E1": 0.0,
        "E2": 0.0,
    }

    pretest_rules = [("A3", "A2", "A1"),
                     ("A4", "A3", "A2"),
                     ("B1.2", "B1.1", "B1.3"),
                     ("B1.3", "B1.1", "B1.2"),
                     ("B1.5", "C1", "B1.3"),
                     ("B2.4.1", "B2.4.2", "B2.3"),
                     ("B2.4.2", "B2.4.1", "B2.3"),
                     ("B2.5", "B2.1", "B2.3"),
                     ("C3.1", "C3.2", "C1"),
                     ("C3.2", "C3.1", "C1"),
                     ("C6.1", "C6.2", "C4.1"),
                     ("C6.2", "C6.1", "C4.1"),
                     ("C6.3.1", "B2.3", "B2.5"),
                     ("C7", "C6.1", "D1"),
                     ("C8", "D3", "C1"),
                     ("D1", "C7", "C6.1")
                     ]

    def __init__(self, user, threshold=0.75, necReps=4):
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
        self.dynamicNet = DynamicNet(self, self.user)
        self.staticNet = StaticNet(self.dynamicNet)


    def init_rules(self):
        """Initialize active rules for user."""

        # create correct rules
        for r in Rule.objects.all():
            ur = UserRule(rule=r, user=self.user, active=False,
                              dynamicnet_active=False, staticnet=self.start_values.get(r.code,0))
            ur.save()

    def activate_first_rule(self):
        """Activate the first rule."""

        new_rule = Rule.objects.get(code="A1")
        ur = UserRule.objects.get(rule=new_rule, user=self.user)
        ur.dynamicnet_current = True
        ur.dynamicnet_active = True
        ur.save()

        # other way over findNewRule
        # new_rule = self.findNextRule()
        # ur = UserRule.objects.get(rule=new_rule, user = self.user)
        # ur.dynamicnet_current = True
        # ur.dynamicnet_active = True
        # ur.save()

        self.user.rules_activated_count = 1  # activate first rule for next request
        self.user.save()
        return new_rule

    def update(self, rule, taskNumber, correct):
        """
        updates the static model
        should be called if the current focus rule is over threshold
        :param DynamicNet: current dynamic net which shall be used to update static net
        :param StaticNet: network containing all rules, shall be updated with values from Dynamic net
        :return: new updated version of the static net
        """
        #access correct node from net
        net = self.dynamicNet.Net
        tasknode = None
        for node in net:
            if node.ruleCode == rule.code:
                tasknode = node
                tasknode.storeAnswer(taskNumber, correct)
                break
            else:
                pass


    def process_pretest(self):
        """Process the pretest results. For every positive result set corresponding rule as active in dynamic net."""
        count_pos=0
        for pretest_result in UserPretest.objects.filter(user=self.user):  # all pretest results for this user
            print(pretest_result)
            if pretest_result.result:  # is it a positive result?
                ur = UserRule.objects.get(rule=pretest_result.rule, user=self.user)  # fetch UserRule object
                if not ur.dynamicnet_active:
                    count_pos += 1 # count as newly activated rule
                ur.dynamicnet_active = True  # set as active in user's dynamic net
                ur.active = True # TODO: check: not needed for bayes strategy?
                ur.save()  # and store back to db
        # increase level for user
        self.user.rules_activated_count += count_pos
        self.user.save()

        return self.activate_first_rule() #todo could this work with find_next_rule function

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
            if i.ur.dynamicnet_active & (not i.known()):
                    possibleRules.append(i)
        if possibleRules: # if there are forgotten rules
            nextRule = possibleRules[0]
            assert isinstance(nextRule,DynamicNode)
            for i in possibleRules:
                if i.value < nextRule.value:
                    nextRule = i # and  choose the one with the worst performance

            if nextRule.ur.dynamicnet_count < self.necReps:  # if the rule was already in the iniial dynamic net, jus show the rule
                # introduce the rule
                reminder = False
                return nextRule.ur.rule, reminder
            else:
                reminder = True
            return nextRule.ur.rule, reminder

        #if all rules in the dynamic net are known choose an appropriate next rule from the dynamic net
        #else:
        minValue = 1
        min_node = None
        for i in UserRule.objects.filter(user=self.user, dynamicnet_active=False):
            node = DynamicNode(BayesStrategy,self.user, i.rule.code, self.dynamicNet)
            if node.value < minValue:
                minValue = node.value
                if node.ruleCode.startswith("E"):
                    pass
                else:
                    minValue = node.value
                    min_node = node
        nextRule = Rule.objects.get(code=min_node.ruleCode)
        return nextRule, False

    def get_active_rules(self):
        """Return currently active rules, at most 5."""
        # limit = min(self.user.rules_activated_count, 5)
        # res = UserRule.objects.filter(user=self.user, active=1).order_by('box')[:limit]
        # return res
        # returns UserRuleObjects
        # choose thoose under 85% performance, if more sort them
        weak = list()
        Net = self.dynamicNet.Net
        for i in Net: #append all rules the user does not know yet
            if not i.known():
                weak.append(i.ur)
        if len(weak) < 5: #if there are less than 5 rules, look for rules with a performance lower than 85%
            weaker = list()
            for rule in Net:
                if rule.get_value() < .85 and i.get_value() > 0.75 : #make sure it is not in list yet
                    weaker.append(rule.ur)
        #if there are still less than 5 rules just return as it is
        return weak


    def findNextRule(self): #returns Rule object
        #     """
        #     function for selecting the next rule.
        #     Considers "forgotten" rules (rules below threshold in dynamic net) first
        #     :return: next rule to be presented, True if rule is a reminder, false if it is a new rule
        #     """
        possibleRules = list()
        next_Rule = None

        #first check wheather there is a forgotten rule
        #look for all forgotten rules
        for i in self.dynamicNet.Net:
            if i.ur.dynamicnet_active & (not i.known()): #is there a rule which is active and not known
                possibleRules.append(i)
        if possibleRules: # if there are forgotten rules
            nextRule = possibleRules[0]
            assert isinstance(nextRule,DynamicNode)
            for i in possibleRules:
                if i.value < nextRule.value:
                    nextRule = i # and  choose the one with the worst performance

            #todo compare node with list from intro test -> is this the right way to check whether or not node was
            #activated by pretest?
            if UserPretest.objects.filter(user=self.user, rule=nextRule.ur.rule, result=True): # if the rule was already in the initial dynamic net, jus show the rule
                # introduce the rule
                reminder = False
                return nextRule.ur.rule, reminder
            else:
                reminder = True
            return nextRule.ur.rule, reminder

        #check the static net for the next rule to be selected

        self.staticNet.updateStatic(self.dynamicNet)
        activeNodes = UserRule.objects.filter(user=self.user, dynamicnet_active=True)
        activeCodes = list()
        for i in activeNodes:
            activeCodes.append(i.rule.code)
        #get the values for the three sections
        auf = self.staticNet.aufValue
        zus = self.staticNet.zusValue
        teil = self.staticNet.teilValue
        worstnode  = min(auf,zus,teil)

        #and choose the section the user has the lowest score in

        if self.staticNet.aufValue == worstnode:
            possibleRules = self.staticNet.auf
        elif self.staticNet.teilValue  == worstnode:
            possibleRules = self.staticNet.teil
        elif self.staticNet.zusValue  == worstnode:
            possibleRules = self.staticNet.zus
        else:
            raise RuntimeError("No next parent to select")

        #and the rule which has the highest prior probability (most likely to be learned
        possibleRules = set(possibleRules) - set(activeCodes) #exclude all active nodes from the list of possible rules

        if not possibleRules: # aera with lowest value (worstnode) is already activated completely
            nextRule, reminder = self.selectNewRule()
            return nextRule, reminder

        maxValue = 0
        max_node = None
        for i in possibleRules:
            try:
                value = BayesStrategy.start_values[i]
            except KeyError:
                pass
            if value > maxValue:
                maxValue = value
                max_node = i
        nextRule = Rule.objects.get(code=max_node)
        return nextRule, False

    def progress(self):
        """
        method needs to activate userRule by userRule.active = true
        :param self:
        :return: the new rule and whether the user is finished, and if it was a forgotten rule (3 values)
        """
        # three cases:
        # 1. User is finished, return false true false
        # 2. User is not finished but needs a new rule, return new rule and false and if it is a reminder
        # 3. User still needs to practise current rule, return false false false

        #get a count of all KNOWN rules -> if activated count > 33 all rules are known and not only activated!
        self.user.rules_activated_count = self.dynamicNet.count_known()+1
        self.user.save()
        # Is user already finished?
        if self.user.rules_activated_count == 33:
            return False, True, False  # new rule = false, finished = true

        # check the current rule
        currentRule = self.dynamicNet.current
        assert isinstance(currentRule, DynamicNode)

        # if it is known, find a new rule
        if currentRule.known():
            newRule,forgotten = self.findNextRule()
            nextur = UserRule.objects.get(user=self.user, rule=newRule)
            nextur.dynamicnet_active = True
            nextur.save()
            self.dynamicNet.setCurrent(newRule)
            #set rule active
            #nodeToActive = self.getNodefromNet(newRule)
            #nodeToActive.activateNode()
            print("new rule passed")
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

        RuleNodes = self.dynamicNet.Net # contains a list of all rule nodes
        assert isinstance(self.dynamicNet, DynamicNet)
        currentRule = self.dynamicNet.current.ruleCode


        pool = list()
        pool.extend(repeat(currentRule,30))
        weakRules = list() #contains all rules under 80%
        #create a pool of rules with different weights, makes it more likely to select weak rules
        for node in RuleNodes:
            assert isinstance(node, DynamicNode)
            assert isinstance(node.value, float)
            if node.value < 0.75:
                pool.extend(repeat(node.ruleCode, 15))
                weakRules.append(node.ruleCode)
            elif node.value < 0.8:
                pool.extend(repeat(node.ruleCode, 8))
                weakRules.append(node.ruleCode)
            elif node.value < 0.85:
                pool.extend(repeat(node.ruleCode, 4))
            elif node.value < 0.9:
                pool.extend(repeat(node.ruleCode, 3))
            elif node.value < 0.95:
                pool.extend(repeat(node.ruleCode, 2))
            elif node.value <= 1:
                pool.extend(repeat(node.ruleCode, 1))

        # add error rules if more than 4 rules
        if len(RuleNodes) >= 4:
            pool.append("E1")
            pool.append("E2")


        random.shuffle(pool) # shuffle the elements in the list
        print("pool is",pool)
        codeOfnewRule = pool[0] #select the first element from the shuffled list
        rule_obj = Rule.objects.filter(code=codeOfnewRule)  # and access the rule object

        possible_sentences = list() #contains SentenceRuleObjects
        contains = False
        activeRules = list()

        for node in self.dynamicNet.Net:
            activeRules.append(node.ur.rule.code)

        # check all active sentences that include a position for the selected rule
        for sr in SentenceRule.objects.filter(rule=rule_obj[0], sentence__active=True).all():
            contains = True
            contained_rules = list()
            for i in sr.sentence.rules.all():
                contained_rules.append(i.code)

            #check weather the sentence contains rules not activated by the user
            if set(contained_rules).difference(set(activeRules)):
                contains = False

            if contains:
                try:
                    us = UserSentence.objects.get(user=self.user, sentence=sr.sentence)
                    count = us.count
                except UserSentence.MultipleObjectsReturned:  # shouldn't happen: multiple database entries
                    count = 0
                except UserSentence.DoesNotExist:  # No counter for that sentence yet
                    count = 0
                possible_sentences.append([sr, count])  # store all possible sentences

        if len(possible_sentences) == 0:  # HACK: No sentence? Try again # TODO: find a real solution
            print("HACK! Try another sentence...")
            return self.roulette_wheel_selection()

        # pick least often used of the possible sentences
        possible_sentences.sort(key=lambda sentence: sentence[1])  # sort ascending by counts

        #todo does this really work? Never reached so far!

        # are there possible sentences containing a weak rule?
        priorSentence = list()
        for i in possible_sentences:
            rulesOfSentence = i[0].rule.code
            if len(rulesOfSentence) > 2:  # if sentence contains more than two rules
                union = list(set().union(rulesOfSentence, weakRules))
                if len(union) > 1:  # if there is a greater union than 1, copy directly
                    priorSentence.append(i[0])

                else:
                    assert isinstance(union[0], Rule)  # otherwise check that the union is not the selected rule
                    # (union[0].code == rule_obj would happen, if the current selected rule is a weak one
                    if union[
                        0].code != rule_obj:  # in this case we rule_obj is not a weak one and we have only one match
                        # with a weak rule
                        priorSentence.append(i[0])

        sentence = None
        if possible_sentences[0][1] == 0:  # first use all sentences at least once
            num = 1
            sentence = random.choice(possible_sentences[:num])[0]  # i.e. if least used sentence has zero count, use it
        # otherwise choose a sentence which contains a weak rules
        elif len(priorSentence) == 1:
            sentence = priorSentence[0]
        elif len(priorSentence) > 1:
            ran = random.randint(0, len(priorSentence) - 1)
            sentence = priorSentence[ran]
        else:
            num = min(3, len(possible_sentences))  # otherwise return one sentence which is used less than 3 times
            sentence = random.choice(possible_sentences[:num])[0]

        return sentence

    # def update_rank(self, staticModel):
    #     """
    #     :param staticModel:
    #     :return: rank (0-3) of user
    #     """
    #     assert (isinstance(staticModel, StaticNet))
    #     overall = staticModel.overall
    #     auf = staticModel.sections['Aufzaehlung'] > self.threshold
    #     teil = staticModel.sections['Teilsaetze'] > self.threshold
    #     zus = staticModel.sections['Zusaetze'] > self.threshold
    #     twoComplete = (auf & teil)|(teil & zus) |(auf & zus)
    #     oneComplete = auf|teil|zus
    #
    #
    #     #Kommakoenig if above threshold
    #     if overall > self.threshold:
    #         return 3
    #     #Kommakommandant if 10% under threshold or 2 sections over threshold
    #     if (overall > (self.threshold*0,9) | twoComplete):
    #         return 2
    #     # Kommakoener if 0,8 percent uner threshold or one complete section
    #     if (overall > (self.threshold*0,8) | oneComplete):
    #         return 1
    #     # Kommachaot if 0,7 percent uner threshold or one complete section
    #     else: return 0

    def getNodefromNet(self, rule):
        for node in self.dynamicNet.Net:
            if node.ruleCode == rule.code:
                return node

    def debug_output(self):
        out="<table><tr><td>Rule</td><td>staticnet</td><td>dynactive</td><td>dyncurrent</td>"+\
            "<td>dyncount</td><td>history1</td><td>history2</td><td>history3</td></tr>\n";
        for r in Rule.objects.all():
            try:
                ur = UserRule.objects.get(rule=r, user=self.user)
                out += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>".format(
                    ur.rule.code, ur.staticnet, ur.dynamicnet_active, ur.dynamicnet_current, ur.dynamicnet_count)
                out += "<td>"+bin(ur.dynamicnet_history1)+"</td><td>"+bin(ur.dynamicnet_history2)+"</td><td>" + \
                   bin(ur.dynamicnet_history3)+"</td></tr>\n"
            except UserRule.DoesNotExist:
                pass
        out += "</table>\n"
        return out
