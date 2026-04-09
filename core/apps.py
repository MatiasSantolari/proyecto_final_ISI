from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_datos_iniciales_admin(sender, **kwargs):
    from core.models import Departamento, Cargo, CargoDepartamento
    
    dep_admin, created_dep = Departamento.objects.get_or_create(
        nombre="ADMIN",
        defaults={'descripcion': 'Departamento administrativo del sistema'}
    )

    cargo_admin, created_car = Cargo.objects.get_or_create(
        nombre="ADMIN",
        defaults={'descripcion': 'Cargo de administrador general'}
    )

    rel, created_rel = CargoDepartamento.objects.get_or_create(
        cargo=cargo_admin,
        departamento=dep_admin,
        defaults={'vacante': 999, 'visible': True}
    )

    if created_dep or created_car or created_rel:
        print("Datos de administración inicializados correctamente.")

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals
        
        post_migrate.connect(crear_datos_iniciales_admin, sender=self)
