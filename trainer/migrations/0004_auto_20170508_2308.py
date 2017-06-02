# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-08 21:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0003_auto_20170420_1142'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='mkdate',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='solution',
            name='type',
            field=models.CharField(default=django.utils.timezone.now, max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='solution',
            name='solution',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='solution',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainer.User'),
        ),
    ]