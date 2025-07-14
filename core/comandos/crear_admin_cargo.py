from django.core.management.base import BaseCommand
from core.models import Cargo

class Command(BaseCommand):
    help = 'Crea el cargo Administrador con es_jefe y es_gerente en True'

    def handle(self, *args, **kwargs):
        cargo, creado = Cargo.objects.get_or_create(
            nombre='ADMIN',
            defaults={'es_jefe': True, 'es_gerente': True}
        )

        if creado:
            self.stdout.write(self.style.SUCCESS('Cargo "Administrador" creado correctamente.'))
        else:
            self.stdout.write(self.style.WARNING('El cargo "Administrador" ya existe.'))