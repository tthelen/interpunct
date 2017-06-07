from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Sentence, Solution, Rule, SentenceRule, User, UserRule, SolutionRule, UserSentence

admin.site.register(Sentence)
admin.site.register(SentenceRule)
admin.site.register(Solution)
admin.site.register(SolutionRule)
admin.site.register(Rule)
admin.site.register(User)
admin.site.register(UserRule)
admin.site.register(UserSentence)

