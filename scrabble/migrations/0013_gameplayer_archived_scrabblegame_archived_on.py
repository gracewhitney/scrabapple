# Generated by Django 4.2.10 on 2025-01-12 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrabble', '0012_gameplayer_winner'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameplayer',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scrabblegame',
            name='archived_on',
            field=models.DateTimeField(null=True),
        ),
    ]
