from django.db import models
import uuid

from events.models import Event

# Create your models here.
class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(default=0)
    sales_start = models.DateTimeField(blank=True)
    sales_end = models.DateTimeField(blank=True)
    quota = models.PositiveIntegerField(default=0)
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE)