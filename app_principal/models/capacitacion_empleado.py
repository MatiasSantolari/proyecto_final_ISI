from django.db import models
from django.apps import apps 

class CapacitacionEmpleado(models.Model):
    id_capacitacion = models.ForeignKey('app_principal.Capacitacion', on_delete=models.CASCADE, db_column="id_capacitacion")
    id_empleado = models.ForeignKey('app_principal.Empleado', on_delete=models.CASCADE, db_column="id_empleado")
    fecha_inscripcion = models.DateField()
    estado = models.CharField(max_length=50)

    class Meta:
        db_table = "capacitacion_empleado"
        unique_together = ("id_capacitacion", "id_empleado")

    def __str__(self):
        Empleado = apps.get_model('app_principal', 'Empleado')
        empleado = Empleado.objects.get(id=self.id_empleado_id)
        return f"{self.id_empleado.persona.nombre} - {self.id_capacitacion.nombre}"