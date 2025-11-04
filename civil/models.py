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
    first_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth_place = models.CharField(max_length=100)
    birthday = models.DateTimeField()
    is_alive = models.BooleanField(default=True)
    is_married = models.BooleanField(default=False)
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
        text = _("%(first_name)s %(last_name)s").strip() if self.first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.last_name, "first_name": self.first_name or ''}

    @property
    def birthday_is_date(self):
        birthday = self.birthday.astimezone(timezone(timedelta(hours=3)))
        return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True

    def __str__(self):
        text = _("%(first_name)s %(last_name)s").strip() if self.first_name else _("%(last_name)s").strip()
        return text % {"last_name": self.last_name, "first_name": self.first_name or ''}

class BirthCertificate(models.Model):
    CERTIFICATE_TYPES = {
        'N': _('Birth'),
        'R': _('Birth and Recognition')
    }
    number = models.IntegerField(default=0)
    born = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="birth_born")
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="birth_father", null=True,)
    father_carreer = models.CharField(max_length=80, null=True)
    father_address = models.CharField(max_length=100, null=True)
    mother = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="birth_mother")
    mother_carreer = models.CharField(max_length=80)
    mother_address = models.CharField(max_length=100, default="Betsiaka")
    declarer = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name='birth_declarer')
    declarer_relationship = models.CharField(max_length=80)
    declarer_carreer = models.CharField(max_length=80)
    declarer_address = models.CharField(max_length=100, default="Betsiaka")
    declarer_was_present = models.BooleanField()
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="birth_responsible_role")
    responsible_staff_name = models.CharField(max_length=100, default="TEXNAS Marie Edonisse Henri")
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="birth_fokotany", default=3)
    certificate_type = models.CharField(max_length=1, choices=CERTIFICATE_TYPES)
    was_alive = models.BooleanField(default=True)
    date_declaration = models.DateTimeField()
    date_register = models.DateTimeField(null=True)
    date_recognization = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['born', 'father', 'mother', 'declarer'],
                name='unique_birth_certificate'
            )
        ]

    def __str__(self):
        if self.born.gender == "M":
            text = _("%(born)s born at %(birthday)s son of %(father)s%(mother)s declared by %(declarer)s, %(relationship)s, at %(date_register)s") 
        else:
            text = _("%(born)s born at %(birthday)s daughter of %(father)s%(mother)s declared by %(declarer)s, %(relationship)s, at %(date_register)s")
        return text % {"born": self.born.full_name, "birthday": self.born.birthday, "father": self.father.__str__() + _(" and ") if self.father else '', "mother": self.mother, "declarer": self.declarer, "relationship": self.declarer_relationship, "date_register": self.date_register}

    @property
    def birth_type(self):
        return self.CERTIFICATE_TYPES[self.certificate_type]
    
    @property
    def numero(self):
        return str(self.number).zfill(3)

    @property
    def pk_str(self):
        return str(self.pk).zfill(9)

class BirthCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    
    # Relation avec le certificat
    certificate = models.ForeignKey(
        BirthCertificate, 
        on_delete=models.CASCADE, 
        related_name="document_birth",
    )
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="document_birth_father", null=True,)
    father_carreer = models.CharField(max_length=80, null=True)
    father_address = models.CharField(max_length=100, null=True)
    mother_carreer = models.CharField(max_length=80)
    mother_address = models.CharField(max_length=100)
    declarer_carreer = models.CharField(max_length=80)
    declarer_address = models.CharField(max_length=100)
    was_alive = models.BooleanField(default=True)
    date_register = models.DateTimeField(null=True)
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
        return _("Birth Certificate - %(number)s") % {"number": self.document_number}   
    
    def get_absolute_url(self):
        return reverse('certificate-preview', kwargs={'pk': self.pk})

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
    def birth_type(self):
        return self.certificate.birth_type
    
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
    def document_number(self):
        return self.certificate.numero

class DeathCertificate(models.Model):
    number = models.IntegerField(default=0)
    dead = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_dead")
    death_day = models.DateTimeField()
    death_place = models.CharField(max_length=100)
    was_born = models.BooleanField(default=True)
    dead_carreer = models.CharField(max_length=80, null=True)
    dead_address = models.CharField(max_length=100, null=True)
    father = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name="death_father", null=True,)
    father_full_name = models.CharField(max_length=120, null=True)
    father_is_alive = models.BooleanField(null=True)
    mother = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_mother", null=True,)
    mother_full_name = models.CharField(max_length=120, null=True)
    mother_is_alive = models.BooleanField(null=True)
    declarer = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="death_declarer")
    declarer_relationship = models.CharField(max_length=80)
    declarer_was_present = models.BooleanField()
    declarer_carreer = models.CharField(max_length=80)
    declarer_address = models.CharField(max_length=100, default="Betsiaka")
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="death_responsible_role")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="death_fokotany", default=0)
    date_register = models.DateTimeField(null=True)
    date_declaration = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dead', 'declarer', 'responsible_staff', 'fokotany'],
                name='unique_death_certificate'
            )
        ]

    @property
    def numero(self):
        return str(self.number).zfill(3)

    def __str__(self):
        if self.dead.gender == "M":
            text = _("%(dead)s dead at %(death_day)s son of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s") 
        else:
            text = _("%(dead)s dead at %(death_day)s daughter of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s")
        return text % {"dead": self.dead, "death_day": self.death_day, "father": self.father_full_name or '', "mother": self.mother_full_name or '', "declarer": self.declarer, "date_declaration": self.date_declaration}


class DeathCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    
    # Relation avec le certificat
    certificate = models.ForeignKey(
        DeathCertificate, 
        on_delete=models.CASCADE, 
        related_name="document_death",
    )
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
        return _("Birth Certificate - %(number)s") % {"number": self.document_number}   
    
    def get_absolute_url(self):
        return reverse('certificate-preview', kwargs={'pk': self.pk})

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
    def birth_type(self):
        return _("Death")
    
    @property
    def type_cert(self):
        return 'death_doc'
    
    @property
    def is_validated(self):
        return self.status == 'V'
    
    @property
    def can_edit(self):
        return self.status == 'D'
    
    @property
    def can_delete(self):
        return self.status in [
            'D', 
            # 'V',
        ]
    
    @property
    def filled_pk(self):
        return str(self.pk).zfill(9)
    
    @property
    def document_number(self):
        return self.certificate.numero

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