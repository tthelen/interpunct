# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-01 20:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('trainer', '0013_remove_rule_paragraph'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='django_user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
