from django.db import models

from django.utils.translation import gettext_lazy as  _

from account.models import User


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

class Staff(models.Model):
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birthday = models.DateTimeField()
    contact_1 = models.CharField(max_length=10)
    contact_2 = models.CharField(max_length=10, null=True)
    date_joined = models.DateField(auto_now_add=True,)
    date_modificated = models.DateField(auto_now=True,)
    date_fired = models.DateField(null=True)
    is_fired = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['last_name', 'first_name', 'gender', 'birthday'],
                name='unique_staff'
            )
        ]

    def __str__(self):
        return _("%(first_name)s %(last_name)s") % {"first_name": self.first_name, "last_name": self.last_name}

class Application(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField(max_length=200)

    def __str__(self):
        return self.title.title()

class Service(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title.title()

class Role(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    app = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    access = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_boss = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'service'],
                name='unique_role'
            )
        ]

    def __str__(self):
        return _("%(staff)s, %(title)s") % {"staff": self.staff, "title": self.title}

class Common(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    district = models.CharField(max_length=80)