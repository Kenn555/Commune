from django import template
from django.utils.translation import gettext as  _


register = template.Library()

@register.filter
def full_name(last_name:str, first_name:str):
    if first_name == '' or not first_name:
        text = _("%(last_name)s")
    else:
        text = _("%(first_name)s %(last_name)s")
    return text % {'first_name': first_name, 'last_name': last_name}