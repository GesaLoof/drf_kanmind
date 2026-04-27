from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    title = models.CharField(max_length=255)
    member_count = models.IntegerField()
    ticket_count = models.IntegerField(blank=True, default=0)
    tasks_to_do_count = models.IntegerField(blank=True, default=0)
    tasks_high_prio_count = models.CharField(max_length=50, blank=True, default=0)
    owner_id = models.IntegerField()

    def __str__(self):
        return f"{self.title} ({self.category})"