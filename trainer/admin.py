from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Sentence, Solution, Rule, SentenceRule, User

admin.site.register(Sentence)
admin.site.register(Solution)
admin.site.register(Rule)
admin.site.register(SentenceRule)
admin.site.register(User)
