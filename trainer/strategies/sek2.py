from trainer.models import Rule, UserRule, SentenceRule, UserSentence, Sentence
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


    def get_next_task(self):
        "Return tupel (rule, sentence) for next task."

        codes = [None, "A1", "B1", "C1"]
        rule = Rule.objects.get(code=codes[self.user.sek2_rule])

        # get all sentences for this rule
        sentence = Sentence.objects.get(part=self.user.sek2_rule, level=self.user.sek2_level, extra=False, active=True)

        return (rule, sentence)

    def update(self, rule, mode, correct):

        self.user.sek2_level += 1
        self.user.save()

