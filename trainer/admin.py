from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Sentence, Solution, User

admin.site.register(Sentence)
admin.site.register(Solution)
admin.site.register(User)
