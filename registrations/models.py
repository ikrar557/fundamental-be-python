import uuid

from django.db import models

from core.models import User
from tickets.models import Ticket

# Create your models here.
class Registration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    ticket_id = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)