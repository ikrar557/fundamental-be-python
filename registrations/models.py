import uuid

from django.db import models

from core.models import User
from tickets.models import Ticket

# TODO: Tambahkan konfigurasi untuk Mengirimkan email reminder event ke pengguna yang order tiket h-2 jam sebelum event
# menggunakan celery beat
# Create your models here.
class Registration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    ticket_id = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)