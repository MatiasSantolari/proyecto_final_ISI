import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    if value:
        return os.path.basename(value)
    return ''