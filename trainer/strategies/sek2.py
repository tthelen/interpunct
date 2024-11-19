from trainer.models import Rule, UserRule, SentenceRule, UserSentence, Sentence, Solution
import random


class Sek2Strategy:
    """The strategy for sek2 rules, Bachelor Thesis Lissen Westendorf."""

    def __init__(self, user):
        self.user = user

        # order of rules (increasing difficulty)
        self.rule_order = [
        "A1",
        "B1",
        "C1"
        ]

    def init_rules(self):
        """Initialize active rules for user."""

        # create correct rules
        for r in self.rule_order:
            ur, created = UserRule.objects.get_or_create(rule=Rule.objects.get(code=r), user=self.user,
                                                         defaults={'active': False})

    def activate_first_rule(self, new_rule=None):
        """Activate first rule"""
        self.init_rules()
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

    def progress(self):
        """Adjust levels etc. and decide if new rule has to be activated.

        returns triple (newrule, finished, forgotten)"""

        if Solution.objects.filter(user=self.user, sek2_rule=self.user.sek2_rule, sek2_level=self.user.sek2_level, correct=True).count() > 0:

            # Finished! Passed last level of last rule
            if self.user.sek2_level == 15 and self.user.sek2_rule==3:
                return (False, True, False)

            # Passed level 15 of a part -> move to next part
            elif self.user.sek2_level == 15:
                self.user.sek2_level = 1
                self.user.sek2_rule += 1
                self.user.rules_activated_count = self.user.sek2_rule
                self.user.save()
                new_rule = Rule.objects.get(code=self.rule_order[self.user.sek2_rule-1])
                return (new_rule,False,False)

            # Passed a level -> move to next level
            else:
                self.user.sek2_level += 1
                self.user.save()
                return (False,False,False)

        return (False,False,False)

    def get_next_task(self):
        "Return tupel (rule, sentence) for next task."

        codes = [None, "A1", "B1", "C1"]
        rule = Rule.objects.get(code=codes[self.user.sek2_rule])

        # if user has correct solutions for this level, switch to next level
        # if not, and there are no solutions at all, pick standard sentence. If there are solutions, pick random extra sentence

        if Solution.objects.filter(user=self.user, sek2_rule=self.user.sek2_rule, sek2_level=self.user.sek2_level).count() == 0:
            sentence = Sentence.objects.get(part=self.user.sek2_rule, level=self.user.sek2_level, extra=False, active=True)
        else:
            sentence = Sentence.objects.filter(part=self.user.sek2_rule, extra=True, active=True).order_by("?").first()

        return (rule, sentence)

    def update(self, rule, mode, correct):

        pass

