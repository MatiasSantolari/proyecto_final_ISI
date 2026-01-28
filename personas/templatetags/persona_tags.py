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
    "en licencia": ("bg-warning text-dark", "En licencia"),
    "suspendido": ("bg-warning text-dark", "Suspendido"),
    "periodo de prueba": ("bg-warning text-dark", "Periodo de Prueba"),
    "jubilado": ("bg-warning text-dark", "Jubilado"),
}


def _badge(value, mapping, default_data):
    key = (value or "").lower()
    return mapping.get(key, default_data)


@register.filter
def tipo_badge_class(tipo):
    return _badge(tipo, TIPO_BADGES, ("bg-secondary", "Sin Rol"))[0]


@register.filter
def tipo_badge_label(tipo):
    return _badge(tipo, TIPO_BADGES, ("bg-secondary", "Sin Rol"))[1]


@register.filter
def estado_badge_class(estado):
    return _badge(estado, ESTADO_BADGES, ("bg-secondary", "Sin Estado"))[0]


@register.filter
def estado_badge_label(estado):
    return _badge(estado, ESTADO_BADGES, ("bg-secondary", "Sin Estado"))[1]
