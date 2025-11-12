import json
from django import template
from core.utils.datatables import get_datatable_definition

register = template.Library()


@register.simple_tag
def datatable_context(name):
    definition = get_datatable_definition(name)
    return {
        "definition": definition,
        "options_json": json.dumps(definition.get("options", {})),
        "filters": {
            filtro["element_id"]: filtro for filtro in definition.get("filters", [])
        },
    }
