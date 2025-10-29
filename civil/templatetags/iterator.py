from django import template
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter
def values(dic:dict, key):
    return dic[key]