from django.db import models

# Create your models here.
    
class Fokotany(models.Model):
    name = models.CharField(max_length=200)
    date_created = models.DateField(auto_now_add=True)
    date_modificated = models.DateField(auto_now=True)

    def __str__(self):
        return f"Fokotany {self.name}"
    ...

class Sector(models.Model):
    name = models.CharField(max_length=200)
    fokotany = models.ForeignKey(Fokotany, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
    date_modificated = models.DateField(auto_now=True)

    def __str__(self):
        return f"Secteur {self.name}"
    ...
