from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Sentence, Solution

admin.site.register(Sentence)
admin.site.register(Solution)
