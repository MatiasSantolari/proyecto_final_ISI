from django import template

register = template.Library()

TIPO_BADGES = {
    "1": ("bg-secondary", "Normal"),
    "2": ("bg-info text-dark", "Empleado"),
    "3": ("bg-primary", "Jefe"),
    "4": ("bg-warning text-dark", "Gerente"),
    "5": ("bg-danger", "Administrador"),
}

ESTADO_BADGES = {
    "1": ("bg-success", "Activo"),
    "2": ("bg-secondary", "Inactivo"),
    "3": ("bg-warning text-dark", "En licencia"),
    "4": ("bg-warning text-dark", "Suspendido"),
    "5": ("bg-warning text-dark", "Periodo de Prueba"),
    "6": ("bg-warning text-dark", "Jubilado"),
}


def _badge(value, mapping, default_label):
    key = (value or "").lower()
    badge_class, label = mapping.get(key, ("bg-secondary", default_label))
    return badge_class, label


@register.filter
def tipo_badge_class(tipo):
    return _badge(tipo, TIPO_BADGES, "Sin Rol")[0]


@register.filter
def tipo_badge_label(tipo):
    return _badge(tipo, TIPO_BADGES, "Sin Rol")[1]


@register.filter
def estado_badge_class(estado):
    return _badge(estado, ESTADO_BADGES, "Sin Estado")[0]


@register.filter
def estado_badge_label(estado):
    return _badge(estado, ESTADO_BADGES, "Sin Estado")[1]
