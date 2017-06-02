# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-04-20 09:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0002_user_rules_activated_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=False)),
                ('box', models.IntegerField(default=0)),
                ('score', models.FloatField(default=0.0)),
                ('total', models.IntegerField(default=0)),
                ('correct', models.IntegerField(default=0)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainer.Rule')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainer.User')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='rules',
            field=models.ManyToManyField(through='trainer.UserRule', to='trainer.Rule'),
        ),
    ]