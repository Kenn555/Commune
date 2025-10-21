from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    date_event = models.DateField()
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

class CommerceEvent(Event):
    marchand = models.CharField(max_length=100)