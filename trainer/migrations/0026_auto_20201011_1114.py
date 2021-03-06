# Generated by Django 3.1.2 on 2020-10-11 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0025_user_data_adaptivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gamification',
            field=models.IntegerField(choices=[(0, 'Level-System'), (1, 'Level-System + individuelles Ranking'), (1, 'Level-System + Gruppen-Ranking'), (1, 'Bayes')], db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='gamification_group',
            field=models.CharField(db_index=True, max_length=32, null=True),
        ),
    ]
