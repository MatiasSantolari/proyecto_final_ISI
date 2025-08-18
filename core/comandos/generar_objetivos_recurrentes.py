from django.core.management.base import BaseCommand
from core.models import Objetivo, ObjetivoEmpleado, Empleado, ObjetivoCargo
from datetime import date

'''''
class Command(BaseCommand):
    help = "Genera objetivos recurrentes para cada empleado asignado"

    def handle(self, *args, **kwargs):
        hoy = date.today()
        recurrentes = Objetivo.objects.filter(es_recurrente=True, activo=True)

        total_creados = 0

        for objetivo in recurrentes:
            for obj_emp in objetivo.objetivoempleado_set.all():
                if not ObjetivoEmpleado.objects.filter(
                    objetivo=objetivo,
                    empleado=obj_emp.empleado,
                    fecha_asignacion=hoy
                ).exists():
                    ObjetivoEmpleado.objects.create(
                        objetivo=objetivo,
                        empleado=obj_emp.empleado,
                        estado="en proceso",
                        fecha_asignacion=hoy,
                        completado=False
                    )
                    total_creados += 1

            for obj_cargo in objetivo.objetivocargo_set.all():
                empleados = Empleado.objects.filter(
                    empleadocargo__cargo=obj_cargo.cargo,
                    empleadocargo__fecha_fin__isnull=True
                ).distinct()
                for emp in empleados:
                    if not ObjetivoEmpleado.objects.filter(
                        objetivo=objetivo,
                        empleado=emp,
                        fecha_asignacion=hoy
                    ).exists():
                        ObjetivoEmpleado.objects.create(
                            objetivo=objetivo,
                            empleado=emp,
                            estado="en proceso",
                            fecha_asignacion=hoy,
                            completado=False
                        )
                        total_creados += 1

        self.stdout.write(self.style.SUCCESS(f"Objetivos recurrentes generados: {total_creados}"))
'''''