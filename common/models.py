import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max

from common.managers import UserManager


class TimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def update(self, update_dict=None, **kwargs):
        """ Helper method to update objects """
        if not update_dict:
            update_dict = kwargs
        update_fields = {"updated_on"}
        for k, v in update_dict.items():
            setattr(self, k, v)
            update_fields.add(k)
        self.save(update_fields=update_fields)

    class Meta:
        abstract = True


# Create your models here.
class User(AbstractUser, TimestampedModel):
    email = models.EmailField(unique=True)
    username = None  # disable the AbstractUser.username field

    one_time_passcode = models.CharField(max_length=32, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_short_name(self):
        return self.first_name or self.email

    def completed_games(self):
        return self.game_racks.filter(game__over=True, game__archived_on__isnull=True)

    def in_progress_games(self):
        """Return in-progress games sorted by most recent turn or creation timestamp"""
        racks = self.game_racks.filter(game__over=False)
        return sorted(
            racks,
            key=lambda r: r.game.all_turns().aggregate(latest=Max("created_on"))["latest"] or r.game.created_on,
            reverse=True
        )

    def known_users(self):
        """Users which have been in a game with this user"""
        return User.objects.filter(
            game_racks__game_id__in=self.game_racks.values('game_id')
        ).exclude(id=self.id).distinct('id')