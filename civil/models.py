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
    def status(self):
        return _('alive') if self.is_alive else _('dead')
    
    @property
    def father(self):
        father = None
        birth = BirthCertificate.objects.filter(person=self)
        if self.gender == "M":
            marriage = MarriageCertificate.objects.filter(groom=self)
        elif self.gender == "F":
            marriage = MarriageCertificate.objects.filter(bride=self)
        death = DeathCertificate.objects.filter(person=self)
        
        if birth and birth.first().father:
            father = birth.first().father
        elif birth and birth.first().recognized_by:
            father = birth.first().recognized_by
        elif marriage:
            if self.gender == "M":
                father = self.marriage_certificate.father_groom
            elif self.gender == "F":
                father = self.marriage_certificate.father_groom
        elif death and death.first().father:
            father = death.first().father

        return father
    
    @property
    def mother(self):
        mother = None
        birth = BirthCertificate.objects.filter(person=self)
        if self.gender == "M":
            marriage = MarriageCertificate.objects.filter(groom=self)
        elif self.gender == "F":
            marriage = MarriageCertificate.objects.filter(bride=self)
        death = DeathCertificate.objects.filter(person=self)

        if birth and birth.first().mother:
            mother = birth.first().mother
        elif marriage:
            if self.gender == "M":
                mother = self.marriage_certificate.mother_groom
            elif self.gender == "F":
                mother = self.marriage_certificate.mother_bride
        elif death and death.first().mother:
            mother = death.first().mother

        return mother

    @property
    def is_recognized(self):
        certificate = BirthCertificate.objects.get(person=self)
        return certificate.date_recognization != certificate.date_register

    @property
    def is_married(self):
        if self.gender == "M":
            certificate = MarriageCertificate.objects.filter(groom=self)
        elif self.gender == "F":
            certificate = MarriageCertificate.objects.filter(bride=self)
        return True if certificate else False

    @property
    def is_married_str(self):
        return _("married") if self.is_married else _("did'nt marry")

    @property
    def has_birth_certificate(self):
        return True if BirthCertificate.objects.filter(person=self) else False

    @property
    def has_recognization_certificate(self):
        return True if RecognizationCertificate.objects.filter(person=self) else False

    @property
    def has_marriage_certificate(self):
        return True if MarriageCertificate.objects.filter(bride=self) or MarriageCertificate.objects.filter(groom=self) else False

    @property
    def has_death_certificate(self):
        return True if DeathCertificate.objects.filter(person=self) else False

    @property
    def marriage_certificate(self):
        if self.gender == "F":
            return MarriageCertificate.objects.get(bride=self)
        if self.gender == "M":
            return MarriageCertificate.objects.get(groom=self)

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

    def get_preview_url(self):
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
    
    @property
    def is_recognized(self):
        return True if RecognizationCertificate.objects.filter(person=self.person) else False

    @property
    def can_recognize(self):
        return self.is_recognized == False and self.father == None
    
    @property
    def recognization_numero(self):
        return RecognizationCertificate.objects.get(person=self.person).numero
    
    @property
    def recognized_by(self):
        recognization = RecognizationCertificate.objects.filter(person=self.person)
        return recognization.first().recognized_by if recognization else None
    
    @property
    def date_recognization(self):
        return RecognizationCertificate.objects.get(person=self.person).date_register

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
    person_is_alive = models.BooleanField(default=True)
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
    # Recognization
    is_recognized = models.BooleanField(default=False)
    recognized_by_last_name = models.CharField(max_length=100, null=True, blank=True)
    recognized_by_first_name = models.CharField(max_length=100, null=True, blank=True)
    recognization_numero = models.CharField(max_length=4, null=True)
    date_recognization = models.DateTimeField(null=True)
    # Register
    had_father = models.BooleanField(default=True)
    was_alive = models.BooleanField(default=True)
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="birthdoc_fokotany", default=0)
    responsible_staff_name = models.CharField(max_length=100)
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    date_register = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Métadonnées du document
    is_original = models.BooleanField(default=False)
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_birth_staff", null=True)
    # Statut
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=0)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
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
    def is_juged(self):
        return (self.date_register - self.person_birthday) > timedelta(days=30)
    
    @property
    def is_noted(self):
        print('is_recognized: ',self.is_recognized)
        print('is_juged: ',self.is_juged)
        return self.is_recognized or self.is_juged

class RecognizationCertificate(models.Model):
    number = models.IntegerField(default=0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="recognization_person")
    recognized_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="recognization_father")
    responsible_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name="recognization_responsible")
    date_declaration = models.DateTimeField()
    date_register = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['person', 'recognized_by'],
                name='unique_recognization_certificate'
            )
        ]

    def get_preview_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.person.pk})

    def get_delete_url(self):
        return reverse('civil:recognization-delete', kwargs={'recognization_id': self.pk})

    @property
    def numero(self):
        return str(self.number).zfill(2)

    @property
    def pk_str(self):
        return str(self.pk).zfill(9)

    @property
    def mother(self):
        return BirthCertificate.objects.get(person=self.person).mother
    
    @property
    def father(self):
        return self.recognized_by
    
    @property
    def declarer(self):
        return self.recognized_by

class RecognizationCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    certificate = models.ForeignKey(RecognizationCertificate, on_delete=models.SET_NULL, null=True, related_name="recognizationdoc_certificate")
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
    # Mère
    mother_last_name = models.CharField(max_length=100)
    mother_first_name = models.CharField(max_length=100, null=True, blank=True)
    mother_birth_place = models.CharField(max_length=100)
    mother_birthday = models.DateTimeField()
    mother_carreer = models.CharField(max_length=80)
    mother_address = models.CharField(max_length=100)
    mother_is_alive = models.BooleanField(default=True)
    # Register
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="recognizationdoc_fokotany", default=0)
    responsible_staff_name = models.CharField(max_length=100)
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    date_register = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Métadonnées du document
    is_original = models.BooleanField(default=False)
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_recognization_staff", null=True)
    # Statut
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=0)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
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
        return 'recognization_doc'
    
    @property
    def type_str(self):
        return _('Recognization')
    
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

class DeathCertificate(models.Model):
    number = models.IntegerField(default=0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="death_person")
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
        
    def get_preview_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.person.pk})

    def get_delete_url(self):
        return reverse('civil:death-delete', kwargs={'death_id': self.pk})

    @property
    def numero(self):
        return str(self.number).zfill(2)

    def __str__(self):
        if self.person.gender == "M":
            text = _("%(person)s person at %(death_day)s son of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s") 
        else:
            text = _("%(person)s person at %(death_day)s daughter of %(father)s%(mother)s declared by %(declarer)s at %(date_declaration)s")
        return text % {"person": self.person, "death_day": self.death_day, "father": self.father.full_name or '', "mother": self.mother.full_name or '', "declarer": self.declarer, "date_declaration": self.date_declaration}
    
    @property
    def recognized_by(self):
        recognization = RecognizationCertificate.objects.filter(person=self.person)
        return recognization.first().recognized_by if recognization else None
    
    
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
    is_original = models.BooleanField(default=False)
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_death_staff", null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=0)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
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
    number = models.IntegerField(default=0)
    groom = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_husband")
    bride = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_wife")
    father_groom = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="marriage_groom_father")
    mother_groom = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="marriage_groom_mother")
    father_bride = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="marriage_bride_father")
    mother_bride = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name="marriage_bride_mother")
    witness_groom = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_witness_groom")
    witness_bride = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="marriage_witness_bride")
    wedding_day = models.DateTimeField()
    responsible_staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="marriage_responsible_staff")
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="marriage_fokotany", default=0)
    is_active = models.BooleanField(default=True)
    date_declaration = models.DateTimeField()
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
            "bride": self.bride,
            "wedding_day": self.wedding_day,
            "date_created": self.date_created
        }
        
    def get_preview_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.groom.pk})

    def get_delete_url(self):
        return reverse('civil:marriage-delete', kwargs={'marriage_id': self.pk})
    
    @property
    def numero(self):
        return str(self.number).zfill(2)

    @property
    def pk_str(self):
        return str(self.pk).zfill(9)
    
class MarriageCertificateDocument(models.Model):
    """Modèle pour stocker les documents générés"""
    GENDER_CHOICES = {
        'M': _("Male"),
        'F': _("Female")
    }
    
    STATUS_CHOICES = {
        'D': _('Draft'),
        'V': _('Validated'),
        'C': _('Cancelled'),
    }
    certificate = models.ForeignKey(MarriageCertificate, on_delete=models.SET_NULL, null=True, related_name="marriagedoc_certificate")
    number = models.IntegerField(default=0)
    # Groom
    groom_last_name = models.CharField(max_length=100)
    groom_first_name = models.CharField(max_length=100, null=True, blank=True)
    groom_birth_place = models.CharField(max_length=100)
    groom_birthday = models.DateTimeField()
    groom_carreer = models.CharField(max_length=100, null=True, blank=True)
    groom_address = models.CharField(max_length=100, null=True, blank=True)
    groom_nationality = models.CharField(max_length=100, default="Malagasy")
    # Bride
    bride_last_name = models.CharField(max_length=100)
    bride_first_name = models.CharField(max_length=100, null=True, blank=True)
    bride_birth_place = models.CharField(max_length=100)
    bride_birthday = models.DateTimeField()
    bride_carreer = models.CharField(max_length=100, null=True, blank=True)
    bride_address = models.CharField(max_length=100, null=True, blank=True)
    bride_nationality = models.CharField(max_length=100, default="Malagasy")
    # Père du marié
    father_groom_last_name = models.CharField(max_length=100, null=True, blank=True)
    father_groom_first_name = models.CharField(max_length=100, null=True, blank=True)
    father_groom_birth_place = models.CharField(max_length=100, null=True, blank=True)
    father_groom_birthday = models.DateTimeField(null=True)
    father_groom_carreer = models.CharField(max_length=80, null=True, blank=True)
    father_groom_address = models.CharField(max_length=100, null=True, blank=True)
    father_groom_is_alive = models.BooleanField(default=True)
    # Mère du marié
    mother_groom_last_name = models.CharField(max_length=100, null=True, blank=True)
    mother_groom_first_name = models.CharField(max_length=100, null=True, blank=True)
    mother_groom_birth_place = models.CharField(max_length=100, null=True, blank=True)
    mother_groom_birthday = models.DateTimeField(null=True)
    mother_groom_carreer = models.CharField(max_length=80, null=True, blank=True)
    mother_groom_address = models.CharField(max_length=100, null=True, blank=True)
    mother_groom_is_alive = models.BooleanField(default=True)
    # Père de la mariée
    father_bride_last_name = models.CharField(max_length=100, null=True, blank=True)
    father_bride_first_name = models.CharField(max_length=100, null=True, blank=True)
    father_bride_birth_place = models.CharField(max_length=100, null=True, blank=True)
    father_bride_birthday = models.DateTimeField(null=True)
    father_bride_carreer = models.CharField(max_length=80, null=True, blank=True)
    father_bride_address = models.CharField(max_length=100, null=True, blank=True)
    father_bride_is_alive = models.BooleanField(default=True)
    # Mère de la mariée
    mother_bride_last_name = models.CharField(max_length=100, null=True, blank=True)
    mother_bride_first_name = models.CharField(max_length=100, null=True, blank=True)
    mother_bride_birth_place = models.CharField(max_length=100, null=True, blank=True)
    mother_bride_birthday = models.DateTimeField(null=True)
    mother_bride_carreer = models.CharField(max_length=80, null=True, blank=True)
    mother_bride_address = models.CharField(max_length=100, null=True, blank=True)
    mother_bride_is_alive = models.BooleanField(default=True)
    # témoins du marié
    witness_groom_last_name = models.CharField(max_length=100)
    witness_groom_first_name = models.CharField(max_length=100, null=True, blank=True)
    witness_groom_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    witness_groom_birth_place = models.CharField(max_length=100)
    witness_groom_birthday = models.DateTimeField()
    witness_groom_carreer = models.CharField(max_length=80)
    witness_groom_address = models.CharField(max_length=100)
    # témoins de la mariée
    witness_bride_last_name = models.CharField(max_length=100)
    witness_bride_first_name = models.CharField(max_length=100, null=True, blank=True)
    witness_bride_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    witness_bride_birth_place = models.CharField(max_length=100)
    witness_bride_birthday = models.DateTimeField()
    witness_bride_carreer = models.CharField(max_length=80)
    witness_bride_address = models.CharField(max_length=100)
    # Mariage
    wedding_day = models.DateTimeField()
    # Enregistrement
    fokotany = models.ForeignKey(Fokotany, on_delete=models.DO_NOTHING, related_name="marriagedoc_fokotany", default=0)
    responsible_staff_name = models.CharField(max_length=100)
    responsible_staff_role = models.CharField(max_length=100, default="Ben'ny Tanàna")
    date_register = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # Métadonnées du document
    is_original = models.BooleanField(default=False)
    date_validated = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, related_name="document_marriage_staff", null=True)
    # Statut
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D')
    # Notes
    notes = models.TextField(null=True)
    # Price
    price = models.FloatField(default=0)
    # Many of documents
    num_copy = models.IntegerField(default=1)
    
    def __str__(self):
        return _("Birth Certificate - %(number)s") % {"number": self.numero}   
    
    def get_absolute_url(self):
        return reverse('civil:certificate-preview', kwargs={'pk': self.pk})
    
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
        return 'marriage_doc'
    
    @property
    def type_str(self):
        return _("Marriage")
    
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