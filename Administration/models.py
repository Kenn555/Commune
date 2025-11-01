from datetime import datetime
from gettext import ngettext
from django.db import models

from django.utils.translation import gettext_lazy as  _
from django.utils.translation import gettext_noop

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

class Application(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField(max_length=200)

    def __str__(self):
        return _(self.title).title()

class Service(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    grade = models.IntegerField(default=0)

    def __str__(self):
        return self.title.title()

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    app = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    access = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    grade = models.IntegerField(default=0)
    date_created = models.DateField(auto_now_add=True)
    date_modificated = models.DateField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'access', 'service'],
                name='unique_role'
            )
        ]

    def __str__(self):
        return self.title

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
    email = models.EmailField(max_length=254, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="staff_role")
    last_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="staff_last_role")
    date_joined_last_role = models.DateField(null=True,)
    date_stoped_last_role = models.DateField(null=True)
    date_joined = models.DateField(auto_now_add=True,)
    date_fired = models.DateField(null=True)
    date_modificated = models.DateField(auto_now=True,)
    is_active = models.BooleanField(default=True)
    is_fired = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['last_name', 'first_name', 'gender', 'birthday'],
                name='unique_staff'
            )
        ]

    def __str__(self):
        return _("%(first_name)s %(last_name)s, %(role)s,") % {"first_name": self.first_name, "last_name": self.last_name, "role": self.role or self.last_role}

    @property
    def full_name(self):
        return _("%(first_name)s %(last_name)s").strip() % {"first_name": self.first_name, "last_name": self.last_name}

    @property
    def since(self):
        if datetime.now().year - self.date_joined.year > 0:
            since = int(datetime.now().year - self.date_joined.year)
            return ngettext("%(since)d year", "%(since)d years", since) % {"since": since}
        elif datetime.now().month - self.date_joined.month > 0:
            since = int(datetime.now().month - self.date_joined.month)
            return ngettext("%(since)d month", "%(since)d months", since) % {"since": since}
        elif datetime.now().day - self.date_joined.day > 0:
            since = int(datetime.now().day - self.date_joined.day)
            return ngettext("%(since)d day", "%(since)d days", since) % {"since": since}

class Common(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    district = models.CharField(max_length=80)