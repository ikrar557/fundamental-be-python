import uuid
from core.models import User

from django.db import models

# Create your models here
class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(blank=True)
    status = models.CharField(max_length=25)
    quota = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100)
    organizer_id = models.ForeignKey(User, on_delete=models.CASCADE)

class EventPoster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='posters')
    image = models.ImageField()

    def __str__(self):
        return self.event.name

    class Meta:
        db_table = 'event_poster'