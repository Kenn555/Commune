from django.db import models

# Create your models here.
class ServicePrice(models.Model):
    certificate_price = models.FloatField(default=1000)