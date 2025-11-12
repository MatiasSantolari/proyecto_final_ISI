from django import template

register = template.Library()

TIPO_BADGES = {
    "normal": ("bg-secondary", "Normal"),
    "empleado": ("bg-info text-dark", "Empleado"),
    "jefe": ("bg-primary", "Jefe"),
    "gerente": ("bg-warning text-dark", "Gerente"),
    "admin": ("bg-danger", "Administrador"),
}

ESTADO_BADGES = {
    "activo": ("bg-success", "Activo"),
    "inactivo": ("bg-secondary", "Inactivo"),
    "suspendido": ("bg-warning text-dark", "Suspendido"),
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
