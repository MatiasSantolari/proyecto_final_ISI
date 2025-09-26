from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



@register.filter
def format_ponderacion(value):
    try:
        value = float(value)
        text = str(value)

        if '.' in text:
            decimals = text.split('.')[1]
            if len(decimals) == 1:
                return f"{value:.2f}"
            else:
                return text.rstrip('0').rstrip('.')
        else:
            return f"{value:.2f}"
    except (ValueError, TypeError):
        return value



@register.filter
def dict_get(d, key):
    try:
        key = int(key)
    except (ValueError, TypeError):
        return None
    return d.get(key)
