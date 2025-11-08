from datetime import timedelta, timezone
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as  _

from administration.models import Fokotany, Role, Staff

# Create your models here.
class Person(models.Model):
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth_place = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateTimeField(blank=True, null=True)
    carreer = models.CharField(max_length=80, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    is_alive = models.BooleanField(default=True)
    nationality = models.CharField(max_length=100, default="malagasy", blank=True, null=True)
    is_married = models.BooleanField(default=False)
    is_parent = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'gender', 'birthday'],
                name="person_unique"
            )
        ]

    @property
    def full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.last_name, "first_name": self.first_name or ''}

    @property
    def url_detail(self):
        return reverse("civil:person-detail", kwargs={'person_id': self.pk})

    @property
    def url_modify(self):
        return reverse("civil:person-modify", kwargs={'person_id': self.pk})

    @property
    def url_preview(self):
        return reverse("civil:certificate-preview", kwargs={'pk': self.pk})

    @property
    def pk_str(self):
        return str(self.pk).zfill(9)

    @property
    def have_birth(self):
        return BirthCertificate.objects.get(person=self)

    @property
    def have_death(self):
        return DeathCertificate.objects.get(person=self)

    @property
    def status(self):
        return _('alive') if self.is_alive else _('dead')

    @property
    def is_recognized(self):
        certificate = BirthCertificate.objects.get(person=self)
        return certificate.date_recognization != certificate.date_register

    def __str__(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.last_name, "first_name": self.first_name or ''}

class BirthCertificate(models.Model):
    CERTIFICATE_TYPES = {
        'N': _('Birth'),
        'R': _('Birth and Recognition')
    }
    number = models.IntegerField(default=0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="birth_person")
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="birth_father", null=True,)
    mother = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="birth_mother")
    declarer = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name='birth_declarer')
    declarer_relationship = models.CharField(max_length=80)
    declarer_was_present = models.BooleanField()
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="birth_responsible_staff")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="birth_fokotany", default=3)
    was_alive = models.BooleanField(default=True)
    had_father = models.BooleanField(default=True)
    date_declaration = models.DateTimeField()
    date_register = models.DateTimeField(null=True)
    date_recognization = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['person', 'father', 'mother', 'declarer'],
                name='unique_birth_certificate'
            )
        ]

    def __str__(self):
        if self.person.gender == "M":
            text = _("%(person)s person at %(birthday)s son of %(father)s%(mother)s declared by %(declarer)s, %(relationship)s, at %(date_register)s") 
        else:
            text = _("%(person)s person at %(birthday)s daughter of %(father)s%(mother)s declared by %(declarer)s, %(relationship)s, at %(date_register)s")
        return text % {"person": self.person.full_name, "birthday": self.person.birthday, "father": self.father.__str__() + _(" and ") if self.father else '', "mother": self.mother, "declarer": self.declarer, "relationship": self.declarer_relationship, "date_register": self.date_register}

    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.person.pk})

    def get_delete_url(self):
        return reverse('civil:birth-delete', kwargs={'birth_id': self.pk})

    @property
    def birth_type(self):
        if not self.had_father:
            return 'N'
        elif self.had_father:
            return 'R'
    
    @property
    def numero(self):
        return str(self.number).zfill(2)

    @property
    def pk_str(self):
        return str(self.pk).zfill(9)

class BirthCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }
    CERTIFICATE_TYPES = {
        'N': _('Birth'),
        'R': _('Birth and Recognition')
    }
    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    certificate = models.ForeignKey(BirthCertificate, on_delete=models.SET_NULL, null=True, related_name="birthdoc_certificate")
    birth_type = models.CharField(max_length=1)
    number = models.IntegerField(default=0)
    # Person
    person_last_name = models.CharField(max_length=100)
    person_first_name = models.CharField(max_length=100, null=True, blank=True)
    person_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    person_birth_place = models.CharField(max_length=100)
    person_birthday = models.DateTimeField()
    person_address = models.CharField(max_length=100, null=True, blank=True)
    # Père
    father_last_name = models.CharField(max_length=100, null=True, blank=True)
    father_first_name = models.CharField(max_length=100, null=True, blank=True)
    father_birth_place = models.CharField(max_length=100, null=True, blank=True)
    father_birthday = models.DateTimeField(null=True)
    father_carreer = models.CharField(max_length=80, null=True, blank=True)
    father_address = models.CharField(max_length=100, null=True, blank=True)
    father_is_alive = models.BooleanField(default=True)
    # Mère
    mother_last_name = models.CharField(max_length=100)
    mother_first_name = models.CharField(max_length=100, null=True, blank=True)
    mother_birth_place = models.CharField(max_length=100)
    mother_birthday = models.DateTimeField()
    mother_carreer = models.CharField(max_length=80)
    mother_address = models.CharField(max_length=100)
    mother_is_alive = models.BooleanField(default=True)
    # Déclarant
    declarer_last_name = models.CharField(max_length=100)
    declarer_first_name = models.CharField(max_length=100, null=True, blank=True)
    declarer_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    declarer_birth_place = models.CharField(max_length=100)
    declarer_birthday = models.DateTimeField()
    declarer_carreer = models.CharField(max_length=80)
    declarer_address = models.CharField(max_length=100)
    declarer_relationship = models.CharField(max_length=80)
    declarer_was_present = models.BooleanField()
    # Register
    had_father = models.BooleanField(default=True)
    was_alive = models.BooleanField(default=True)
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="birthdoc_fokotany", default=0)
    responsible_staff_name = models.CharField(max_length=100)
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    date_register = models.DateTimeField(null=True)
    date_recognization = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    client_detail = models.CharField(max_length=120, null=True)
    # Métadonnées du document
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_birth_staff", null=True)
    # Statut
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=1000)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
    @property
    def person_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.person_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.person_last_name, "first_name": self.person_first_name or ''}
    
    @property
    def person_birthday_is_date(self):
        birthday = self.person_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True

    @property
    def father_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.father_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.father_last_name, "first_name": self.father_first_name or ''}
    
    @property
    def father_birthday_is_date(self):
        birthday = self.father_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True
    
    @property
    def mother_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.mother_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.mother_last_name, "first_name": self.mother_first_name or ''}
        
    @property
    def mother_birthday_is_date(self):
        birthday = self.mother_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True
    
    @property
    def declarer_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.declarer_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.declarer_last_name, "first_name": self.declarer_first_name or ''}
        
    @property
    def declarer_birthday_is_date(self):
        birthday = self.declarer_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True

    @property
    def get_price(self):
        return int(self.price) if self.price.is_integer() else self.price
        
    @property
    def get_total_price(self):
        return int(self.price) * int(self.num_copy) if self.price.is_integer() else self.price * self.num_copy
    
    @property
    def status_str(self):
        return self.STATUS_CHOICES[self.status]
    
    @property
    def type_cert(self):
        return 'birth_doc'
    
    @property
    def type_str(self):
        return self.CERTIFICATE_TYPES[self.birth_type]
    
    @property
    def is_validated(self):
        return self.status == 'V'
    
    @property
    def can_edit(self):
        return self.status == 'D'
    
    @property
    def can_delete(self):
        return self.status in [
            'D', # Si le certificat est un brouillon
            # 'V', # Si le certificat a déjà été validé
        ]
    
    @property
    def filled_pk(self):
        return str(self.pk).zfill(9)
    
    @property
    def numero(self):
        return str(self.number).zfill(2)
    
    @property
    def is_noted(self):
        return (not self.had_father and self.father_full_name) or (self.date_register - self.person_birthday) > timedelta(days=30)

    @property
    def is_recognized(self):
        return not self.had_father and self.father_last_name

    @property
    def is_juged(self):
        return (self.date_register - self.person_birthday) > timedelta(days=30)

class DeathCertificate(models.Model):
    number = models.IntegerField(default=0)
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_person")
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="death_father", null=True,)
    mother = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_mother", null=True,)
    declarer = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_declarer")
    declarer_relationship = models.CharField(max_length=80)
    declarer_was_present = models.BooleanField()
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="death_responsible_staff")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="death_fokotany", default=0)
    death_day = models.DateTimeField()
    death_place = models.CharField(max_length=100)
    date_register = models.DateTimeField(null=True)
    date_declaration = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['person', 'declarer', 'responsible_staff', 'fokotany'],
                name='unique_death_certificate'
            )
        ]

    @property
    def numero(self):
        return str(self.number).zfill(2)

    def __str__(self):
        if self.person.gender == "M":
            text = _("%(person)s person at %(death_day)s son of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s") 
        else:
            text = _("%(person)s person at %(death_day)s daughter of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s")
        return text % {"person": self.person, "death_day": self.death_day, "father": self.father.full_name or '', "mother": self.mother.full_name or '', "declarer": self.declarer, "date_declaration": self.date_declaration}


class DeathCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    certificate = models.ForeignKey(DeathCertificate, on_delete=models.SET_NULL, null=True, related_name="deathdoc_certificate")
    number = models.IntegerField(default=0)
    # Person
    person_last_name = models.CharField(max_length=100)
    person_first_name = models.CharField(max_length=100, null=True, blank=True)
    person_birth_place = models.CharField(max_length=100)
    person_birthday = models.DateTimeField(null=True, blank=True)
    person_carreer = models.CharField(max_length=80, null=True, blank=True)
    person_address = models.CharField(max_length=100, null=True, blank=True)
    # Père
    father_last_name = models.CharField(max_length=100, null=True, blank=True)
    father_first_name = models.CharField(max_length=100, null=True, blank=True)
    father_birth_place = models.CharField(max_length=100, null=True, blank=True)
    father_birthday = models.DateTimeField(null=True, blank=True)
    father_carreer = models.CharField(max_length=80, null=True, blank=True)
    father_address = models.CharField(max_length=100, null=True, blank=True)
    father_is_alive = models.BooleanField(default=True)
    # Mère
    mother_last_name = models.CharField(max_length=100, null=True, blank=True)
    mother_first_name = models.CharField(max_length=100, null=True, blank=True)
    mother_birth_place = models.CharField(max_length=100, null=True, blank=True)
    mother_birthday = models.DateTimeField(null=True)
    mother_carreer = models.CharField(max_length=80, null=True, blank=True)
    mother_address = models.CharField(max_length=100, null=True, blank=True)
    mother_is_alive = models.BooleanField(default=True)
    # Déclarant
    declarer_last_name = models.CharField(max_length=100)
    declarer_first_name = models.CharField(max_length=100, null=True, blank=True)
    declarer_birth_place = models.CharField(max_length=100)
    declarer_birthday = models.DateTimeField()
    declarer_carreer = models.CharField(max_length=80)
    declarer_address = models.CharField(max_length=100)
    declarer_relationship = models.CharField(max_length=80)
    declarer_was_present = models.BooleanField()
    # Register
    death_day = models.DateTimeField()
    death_place = models.CharField(max_length=100)
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="deathdoc_fokotany", default=0)
    responsible_staff_name = models.CharField(max_length=100)
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    date_register = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Métadonnées du document
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_death_staff", null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=1000)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
    @property
    def person_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.person_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.person_last_name, "first_name": self.person_first_name or ''}
    
    @property
    def person_birthday_is_date(self):
        birthday = self.person_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True

    @property
    def father_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.father_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.father_last_name, "first_name": self.father_first_name or ''}
    
    @property
    def father_birthday_is_date(self):
        birthday = self.father_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True
    
    @property
    def mother_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.mother_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.mother_last_name, "first_name": self.mother_first_name or ''}
        
    @property
    def mother_birthday_is_date(self):
        birthday = self.mother_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True
    
    @property
    def declarer_full_name(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.declarer_first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.declarer_last_name, "first_name": self.declarer_first_name or ''}
        
    @property
    def declarer_birthday_is_date(self):
        birthday = self.declarer_birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True

    @property
    def get_price(self):
        return int(self.price) if self.price.is_integer() else self.price
        
    @property
    def get_total_price(self):
        return int(self.price) * int(self.num_copy) if self.price.is_integer() else self.price * self.num_copy
    
    @property
    def status_str(self):
        return self.STATUS_CHOICES[self.status]
    
    @property
    def type_cert(self):
        return 'death_doc'
    
    @property
    def type_str(self):
        return _("Death")
    
    @property
    def is_validated(self):
        return self.status == 'V'
    
    @property
    def can_edit(self):
        return self.status == 'D'
    
    @property
    def can_delete(self):
        return self.status in [
            'D', # Si le certificat est un brouillon
            # 'V', # Si le certificat a déjà été validé
        ]
    
    @property
    def filled_pk(self):
        return str(self.pk).zfill(9)
    
    @property
    def numero(self):
        return str(self.number).zfill(2)

class MarriageCertificate(models.Model):
    groom = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_husband")
    bride = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_wife")
    wedding_day = models.DateTimeField()
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="marriage_responsible_staff")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="marriage_fokotany", default=0)
    is_active = models.BooleanField(default=True)
    date_register = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['groom', 'bride', 'wedding_day'],
                name='unique_marriage_certificate'
            )
        ]

    def __str__(self):
        return _("%(groom)s and %(bride)s married at %(wedding_day)s done at %(date_created)s") % {
            "groom": self.groom,
            "wife": self.bride,
            "wedding_day": self.wedding_day,
            "date_created": self.date_created
        }