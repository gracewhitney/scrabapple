# Generated by Django 4.2.3 on 2023-11-26 19:39

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import scrabble.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scrabble', '0002_gameturn_turn_words_scrabblegame_next_turn_index'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='gameplayer',
            unique_together={('game', 'turn_index'), ('game', 'user')},
        ),
        migrations.AddField(
            model_name='gameplayer',
            name='forfeited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scrabblegame',
            name='over',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='gameturn',
            name='game_player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turns', to='scrabble.gameplayer'),
        ),
        migrations.AlterField(
            model_name='scrabblegame',
            name='board',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='', max_length=2), size=15), default=scrabble.models.get_initial_board, size=15),
        ),
    ]