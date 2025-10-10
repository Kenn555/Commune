from django.db import models
from django.utils.translation import gettext_lazy as  _

from administration.models import Fokotany

# Create your models here.
class Person(models.Model):
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth_place = models.CharField(max_length=100)
    birthday = models.DateTimeField()
    is_parent = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'gender', 'birthday'],
                name="person_unique"
            )
        ]

    @property
    def full_name(self):
        return _("%(first_name)s %(last_name)s").strip() % {"last_name": self.last_name, "first_name": self.first_name or ''}

    def __str__(self):
        return _("%(first_name)s %(last_name)s").strip() % {"last_name": self.last_name, "first_name": self.first_name or ''}

class BirthCertificate(models.Model):
    CERTIFICATE_TYPES = {
        'F': 'Fatherless',
        'N': 'Normal',
        'R': 'Recognition'
    }
    born = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="bith_born")
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="bith_father", null=True,)
    father_carreer = models.CharField(max_length=80, null=True)
    mother = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="bith_mother")
    mother_carreer = models.CharField(max_length=80)
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="birth_fokotany", default=0)
    certificate_type = models.CharField(max_length=1, choices=CERTIFICATE_TYPES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['born', 'father', 'mother'],
                name='unique_birth_certificate'
            )
        ]

    def __str__(self):
        if self.born.gender == "M":
            text = _("%(born)s born at %(birthday)s son of %(father)s%(mother)s done at %(date_created)s") 
        else:
            text = _("%(born)s born at %(birthday)s daughter of %(father)s%(mother)s done at %(date_created)s")
        return text % {"born": self.born, "birthday": self.born.birthday, "father": self.father.__str__() + _(" and ") if self.father else '', "mother": self.mother, "date_created": self.date_created}