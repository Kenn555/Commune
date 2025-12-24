from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    color = models.CharField(
        max_length=20,
        default="#3788d8",
        help_text="Couleur de fond (HEX ou nom CSS)"
    )

    text_color = models.CharField(
        max_length=20,
        default="#ffffff",
        help_text="Couleur du texte"
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'color', 'text_color'],
                name='unique_category_name'
            )
        ]

    def __str__(self):
        return self.name
    
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start = models.DateTimeField()
    end = models.DateTimeField()

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events_category'
    )

    color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Couleur de fond pour le calendrier (ex: red, #FF0000)"
    )
    text_color = models.CharField(
        max_length=20,
        blank=True,
        help_text="Couleur pour le calendrier (ex: red, #FF0000)"
    )

    is_urgent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start']

    def __str__(self):
        return f"{self.title} ({self.start} → {self.end})"

    def duration(self):
        if (self.end - self.start).days > 1:
            return str((self.end - self.start).days) + _("d")
        elif (self.end - self.start).seconds > 3600:
            return str(round((self.end - self.start).seconds/3600)) + _("h")
        elif (self.end - self.start).seconds > 60:
            return str(round((self.end - self.start).seconds/60)) + _("m")
        else:
            return str(round((self.end - self.start).seconds)) + _("s")
    
    def delete_url(self):
        return reverse("events:event-delete", kwargs={'event_id': self.pk})

class Task(models.Model):
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='tasks_event'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    is_done = models.BooleanField(default=False)

    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date limite de la tâche"
    )

    priority = models.PositiveSmallIntegerField(
        default=1,
        help_text="basse, normale, haute"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_done', '-priority', 'due_date']

    def __str__(self):
        return f"{self.title} ({'OK' if self.is_done else 'TODO'})"
