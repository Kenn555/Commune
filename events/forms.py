from django import forms
from django.utils.translation import gettext_lazy as _

from events.models import Category, Event, Task


CLASS_FIELD = """
        w-full bg-transparent border-0 border-b-2 border-b-gray-300
        outline-none font-medium text-base tracking-wider
        focus:outline-none focus:border-b-[#007e3a]
        focus:ring-0 focus:ring-offset-0
    """
    
class EventForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label=_("Title"),
        widget=forms.TextInput(attrs={
            'class': CLASS_FIELD,
            'placeholder': _('Title of the event')
        })
    )

    start = forms.DateTimeField(
        label=_("Start"),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
            'class': CLASS_FIELD,
            'type': 'datetime-local'
            }
        )
    )

    end = forms.DateTimeField(
        label=_("End"),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
            'class': CLASS_FIELD,
            'type': 'datetime-local'
            }
        )
    )

    color = forms.CharField(
        required=False,
        label=_("Background Color"),
        initial="#0000FF",
        widget=forms.TextInput(attrs={
            'class': CLASS_FIELD,
            'type': 'color',
            'style': 'height:40px; padding:0;'
        })
    )

    text_color = forms.CharField(
        required=False,
        label=_("Color"),
        initial='#ffffff',
        widget=forms.TextInput(attrs={
            'class': CLASS_FIELD,
            'type': 'color',
            'style': 'height:40px; padding:0;'
        })
    )

    category = forms.ChoiceField(
        label=_("Category"), 
        choices=Category.objects.all().order_by('pk').values_list('id', 'name').reverse(),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the category")
            }
        )
    )

    description = forms.CharField(
        required=False,
        label=_("Description"),
        widget=forms.Textarea(attrs={
            'class': CLASS_FIELD,
            'rows': 1,
            'placeholder': _('Description of the event')
        })
    )

    is_urgent = forms.BooleanField(
        required=False,
        label=_("Is Urgent"),
        widget=forms.CheckboxInput(attrs={
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')

        if start and end and end <= start:
            raise forms.ValidationError(
                _("Date of 'End' must be after 'Start'.")
            )

        return cleaned_data
    
class TaskForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label=_("Title"),
        widget=forms.TextInput(attrs={
            'class': CLASS_FIELD,
            'placeholder': _('Title of the task')
        })
    )

    due_date = forms.DateTimeField(
        label=_("Start"),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={
            'class': CLASS_FIELD,
            'type': 'datetime-local'
            }
        )
    )

    event = forms.ChoiceField(
        label=_("Event"), 
        choices=Event.objects.all().order_by('end').values_list('id', 'title'),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the event")
            }
        )
    )

    priority = forms.ChoiceField(
        label=_("Priority"), 
        choices=((1, _("Low")), (2, _("Normal")), (3, _("High"))),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the priority")
            }
        )
    )

    description = forms.CharField(
        required=False,
        label=_("Description"),
        widget=forms.Textarea(attrs={
            'class': CLASS_FIELD,
            'rows': 1,
            'placeholder': _('Description of the task')
        })
    )
