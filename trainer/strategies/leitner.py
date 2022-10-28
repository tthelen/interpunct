from trainer.models import Rule, UserRule, SentenceRule, UserSentence, UserPretest
import random


class LeitnerStrategy:
    """A leitner box level progress and sentence selection strategy."""

    def __init__(self, user):

        self.user = user

        # order of rules (increasing difficulty)
        self.rule_order = [
            "A1",  # 1 GLEICHRANG
            "A2",  # 2 ENTGEGEN
            "A4",  # 12 GLEIHRANG KONJUNKT
            "B1.1",  # 3 NEBEN
            "B2.1",  # 4 UMOHNESTATT
            "C1",  # 5 PARANTHESE
            "D1",  # 6 ANREDE/AUSRUF
            "B1.2",  # 7 NEBEN EINLEIT
            "C2",  # 8 APPOSITION
            "A3",  # 9 SATZREIHUNG
            "C5",  # 10 HINWEIS
            "B1.5",  # 11 FORMELHAFT
            "D3",  # 13 BEKTRÄFT
            "B2.2",  # 14
            "C3.1",  # 15
            "B2.3",  # 16
            "C3.2",  # 17
            "B2.4.1",  # 18
            "C4.1",  # 19
            "B2.4.2",  # 20
            "B2.5",  # 21
            "C6.1",  # 22
            "C6.2",  # 23
            "C6.3.1",  # 24
            "C6.3.2",  # 25
            "C6.4",  # 26
            "C7",  # 27
            "B1.3",  # 28 NEBEN KONJUNKT
            "B1.4.1",  # 29
            "B1.4.2",  # 30
        ]

    pretest_rules = [("A1",   "A3",   "C1"),
                     ("A2",   "C4.1", "C1"),
                     ("B1.1", "B1.5", "C5"),
                     ("B2.1", "B2.2", "B2.3"),
                     ("C1",   "C2",   "C5"),
                     ("D1",   "C1",   "A1"),
                     ("B1.2", "B1.1", "B1.5"),
                     ("C2",   "C5",   "C1"),
                     ("A3",   "C4.1", "B2.5"),
                     ("C5",   "C6.1", "C6.2")]

    def init_rules(self):
        """Initialize active rules for user."""

        # create correct rules
        for r in self.rule_order:
            ur, created = UserRule.objects.get_or_create(rule=Rule.objects.get(code=r), user=self.user, defaults={'active':False})
        # create error rules
        ur, created = UserRule.objects.get_or_create(rule=Rule.objects.get(code="E1"), user=self.user, defaults={'active':False})
        ur, created = UserRule.objects.get_or_create(rule=Rule.objects.get(code="E2"), user=self.user, defaults={'active':False})

    def activate_first_rule(self, new_rule=None):
        """Activate first rule"""
        if not new_rule:
            new_rule = Rule.objects.get(code=self.rule_order[0])
        try:
            ur = UserRule.objects.get(rule=new_rule, user=self.user)
        except UserRule.MultipleObjectsReturned:
            urs = UserRule.objects.filter(rule=new_rule, user=self.user)
            ur = urs[0]
            urs[1].delete()
        ur.active = True
        ur.save()

        self.user.rules_activated_count = self.rule_order.index(new_rule.code)+1  # activate first rule for next request
        self.user.save()
        return new_rule

    def process_pretest(self):
        """Process the results of the pretest.
        Problem for current leitner representation: Rule order is fixed. So set level to last level befor first error."""

        self.user.pretest = True
        self.user.save()
        last_pos = -1  # highest position in self.rule_order for whoch the pretest was positive
        new_rule = None
        for rule_idx in range(len(self.rule_order)):
            pretest_result = None
            try:
                pretest_result = UserPretest.objects.get(user=self.user, rule__code=self.rule_order[rule_idx])
                if pretest_result.result:
                    last_pos = rule_idx  # new best position
                    new_ur = UserRule.objects.filter(rule__code=self.rule_order[rule_idx], user=self.user).first()
                    new_ur.active = True  # activate new rule
                    new_ur.box = 4 # lowest box
                    new_ur.save()
                else:
                    # WARNING: pretest must be shorter than rule list, otherwise we might fail here
                    new_rule = Rule.objects.get(code=self.rule_order[rule_idx])
                    break
            except UserPretest.DoesNotExist:
                break

        # increase level for user
        if last_pos+1 > self.user.rules_activated_count:
            self.user.rules_activated_count = last_pos +1
        self.user.save()

        return self.activate_first_rule(new_rule)

    def get_active_rules(self):
        """Return UserRule and examples sentence data for displaying level and expanations.
           At most 5 rules sorted by box position."""

        limit = min(self.user.rules_activated_count, 5)
        res = UserRule.objects.filter(user=self.user, active=1).order_by('box')[:limit]
        return res

    def progress(self):
        """Advance to next level, if appropriate.

        Returns (new_rule, finished?, forgottenrule?)
        new_rule is False if no level progress, the newly activated Rule object otherwise.
        finished is false if not all rules are activated and true if all Rules are activated
        forgotterule is always false here (would enable repeating forgotten rules) # TODO: check if appropriate here
        """

        # bugix: previous version set rule_activated_count too high
        # decrease level or activate first rule
        try:
            check_rule = UserRule.objects.get(user=self.user, rule__code=self.rule_order[self.user.rules_activated_count-1])
        except UserRule.MultipleObjectsReturned:
            urs = UserRule.objects.filter(user=self.user, rule__code=self.rule_order[self.user.rules_activated_count-1])
            check_rule = urs[0]
            urs[1].delete()

        if not check_rule.active:
            if self.user.rules_activated_count>0:
                self.user.rules_activated_count -= 1
                self.user.save()
            else:
                self.activate_first_rule()

        # highest level reached?
        if self.user.rules_activated_count == len(self.rule_order):
            return False, True, False

        # user objects have a property #rules_actived_count, i.e. the level
        # in this strategy, we simply check if the rule for the current level
        # has more than 3 tries, less than half of them wrong
        last_rule = self.rule_order[self.user.rules_activated_count - 1]  # rule code
        #print("Rules activated count: {}".format(self.user.rules_activated_count))
        #print("Last rule: {}".format(last_rule))
        # UserRule objects count a user's tries for a certain rule
        ur = UserRule.objects.get(user=self.user, rule=Rule.objects.get(code=last_rule))
        # advancement criterion: more than 3 tries, less than half of them wrong
        if ur.total >= 4 and ur.correct >= (ur.total / 2):
            self.user.rules_activated_count += 1  # increase level
            self.user.save()  # save to database
            # create and activate new rule for user
            new_rule = Rule.objects.get(code=self.rule_order[self.user.rules_activated_count - 1])
            new_ur = UserRule.objects.get(rule=new_rule, user=self.user)
            new_ur.active = True  # activate new rule
            new_ur.box = 1
            new_ur.save()
            return new_rule, (self.user.rules_activated_count == len(self.rule_order)), False

        return False, False, False

    def roulette_wheel_selection(self):
        """
        gets a new sentence via roulette wheel, chooses random among sentences
        :return: a randomly chosen SentenceRule object
        """

        roulette_list = []
        active_rules = 0
        # for all active rules for current user:
        for ur in UserRule.objects.filter(user=self.user, active=True).all():
            # Spaced repetition algorithm: Each box is half as probable as previous one
            # Each active rule is added 2^n times to the selection list, n = 4-box#
            # Examples:
            # Box 0 (default for new rules): 2^4 = 16 times
            # Box 1: 2^3 = 8 times
            # Box 2: 2^2 = 4 times
            # Box 3: 2^1 = 2 times
            # Box 4: 2^0 = 1 time
            for i in range(2**(4-ur.box)):
                roulette_list.append(ur.rule.code)
            active_rules += 1

        if active_rules >= 4:  # error rules are activated with fourth rule

            for r in Rule.objects.filter(code__startswith='E').all():
                    # all error rules are treated like box 3
                    # TODO: treat error rules like normal rules
                    roulette_list.append(r.code)
                    roulette_list.append(r.code)

        # randomly pick a rule from boxes
        index = random.randint(0, len(roulette_list)-1)
        rule_obj = Rule.objects.filter(code=roulette_list[index])

        # filter out all sentences that have higher rules than current user's progress
        possible_sentences = []
        # check all active sentences taht include a position for the selected rule
        for sr in SentenceRule.objects.filter(rule=rule_obj[0], sentence__active=True).all():
            ok = True
            # check all other rules that this sentence includes
            for r in sr.sentence.rules.all():
                # find rule's position in rule order and compare to current level
                if r.code in self.rule_order and \
                        (self.rule_order.index(r.code) > (self.user.rules_activated_count-1)):
                    ok = False  # too high rule found -> abort checking this rule
                    break
            if ok:
                try:
                    us = UserSentence.objects.get(user=self.user, sentence=sr.sentence)
                    count = us.count
                except UserSentence.MultipleObjectsReturned:  # shouldn't happen: multiple database entries
                    count = 0
                except UserSentence.DoesNotExist:  # No counter for that sentence yet
                    count = 0
                possible_sentences.append([sr, count])  # collect sentence and per user counter for the sentence

        if len(possible_sentences) == 0: # HACK: No sentence? Try again # TODO: find a real solution
            return self.roulette_wheel_selection()

        # pick least often used of the possible sentences
        possible_sentences.sort(key=lambda sentence: (sentence[1], len(sentence[0].sentence.text)))  # sort ascending by counts and length of senetences (in characters)

        if possible_sentences[0][1] == 0:  # first use all sentences at least once
            num = 1                        # i.e. if least used sentence has zero count, use it
        else:
            num = min(3, len(possible_sentences))  # else choose from three least often used

        return random.choice(possible_sentences[:num])[0]  # randomly choose and return SentenceRule object

    def update(self, rule, mode, correctness):
        """Updates internal state of strategy."""
        pass

    def get_active_rules(self):
        return UserRule.objects.filter(user=self.user, active=1)[:5]

    def debug_output(self):
        return "<p>Strategy: Leitner, no debug info</p>"