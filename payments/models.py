import uuid

from django.db import models

from registrations.models import Registration

# Create your models here.
class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    amount_paid = models.PositiveIntegerField(default=0)
    registration_id = models.ForeignKey(Registration, on_delete=models.CASCADE)