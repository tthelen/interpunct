# Generated by Django 3.1.2 on 2020-10-11 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0028_auto_20201011_2233'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(db_index=True, max_length=32)),
                ('mkdate', models.DateTimeField(auto_now_add=True)),
                ('correct', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='GroupScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(db_index=True, max_length=32)),
                ('score', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='gamification',
            field=models.IntegerField(choices=[(0, 'Level-System'), (1, 'Level-System + individuelles Ranking'), (2, 'Level-System + Gruppen-Ranking'), (1, 'Bayes')], db_index=True, default=0),
        ),
    ]
