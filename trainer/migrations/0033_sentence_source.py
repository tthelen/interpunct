# Generated by Django 3.1.2 on 2021-10-04 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainer', '0032_user_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='sentence',
            name='source',
            field=models.CharField(max_length=512, null=True),
        ),
    ]
