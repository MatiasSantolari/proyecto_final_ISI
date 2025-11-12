from django import template
from core.utils.datatables import get_datatable_context

register = template.Library()


@register.simple_tag
def datatable_context(name):
    return get_datatable_context(name)
