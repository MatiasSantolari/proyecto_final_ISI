"""
This app depends on existing persona-related models defined inside
`core.models.persona`. They stay allí por ahora para evitar migraciones,
pero se importan aquí para dejar claro el contrato del módulo.
"""

from core.models.persona import (
    Persona,
    DatoAcademico,
    Certificacion,
    ExperienciaLaboral,
)

__all__ = [
    "Persona",
    "DatoAcademico",
    "Certificacion",
    "ExperienciaLaboral",
]
