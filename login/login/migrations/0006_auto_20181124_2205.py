# Generated by Django 2.0.8 on 2018-11-24 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_auto_20181124_2204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subtask',
            name='result',
            field=models.TextField(max_length=1024),
        ),
    ]
