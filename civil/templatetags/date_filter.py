from datetime import datetime, timedelta, timezone
from django import template
from django.utils.translation import gettext as  _


register = template.Library()

@register.filter
def is_date(date:datetime) -> bool:
    birthday = date.astimezone(timezone(timedelta(hours=3)))
    return False if birthday.day == 1 and birthday.month == 1 and birthday.hour == 0 and birthday.minute == 0 else True