# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-04 19:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0019_auto_20180504_0845'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_current',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_history1',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_history2',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userrule',
            name='dynamicnet_history3',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userrule',
            name='staticnet',
            field=models.FloatField(default=0.0),
        ),
    ]
