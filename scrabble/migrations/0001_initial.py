# Generated by Django 4.2.3 on 2023-10-30 21:06

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import scrabble.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrabbleGame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('letter_bag', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1), default=scrabble.models.get_initial_letter_bag, size=None)),
                ('board', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default='', max_length=1), size=15), default=scrabble.models.get_initial_board, size=15)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GameTurn',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('turn_count', models.IntegerField()),
                ('turn_action', models.CharField(choices=[('play', 'Play'), ('exchange', 'Exchange'), ('pass', 'Pass Turn'), ('forfeit', 'Forfeit')], max_length=32)),
                ('score', models.IntegerField()),
                ('rack_before_turn', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1), size=7)),
                ('game_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turns', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GamePlayer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('rack', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1), size=7)),
                ('score', models.IntegerField(default=0)),
                ('turn_index', models.IntegerField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='racks', to='scrabble.scrabblegame')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='game_racks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('game', 'turn_index')},
            },
        ),
    ]
