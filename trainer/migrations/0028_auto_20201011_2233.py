# Generated by Django 3.1.2 on 2020-10-11 20:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0027_auto_20201011_2153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='gamification_score',
            field=models.IntegerField(db_index=True, default=0),
        ),
        migrations.CreateModel(
            name='UserHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mkdate', models.DateTimeField(auto_now_add=True)),
                ('correct', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainer.user')),
            ],
        ),
    ]
