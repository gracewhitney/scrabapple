# Generated by Django 4.2.3 on 2024-03-03 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrabble', '0008_gameplayer_send_turn_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrabblegame',
            name='use_old_upwords_rules',
            field=models.BooleanField(default=False),
        ),
    ]