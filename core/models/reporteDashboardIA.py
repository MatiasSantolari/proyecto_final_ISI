import os
from django.db import models
from django.conf import settings
from .usuario import Usuario 


def ruta_destino_reporte_ia(instance, filename):
    """
    Genera la ruta organizada por el username del usuario:
    Media/reportesIA/admin/Reporte_Dashboard_2026-05-23.pdf
    """
    import os
    return os.path.join('reportesIA', instance.usuario.rol, filename)

class ReporteDashboardIA(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="Generado por")
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    archivo_pdf = models.FileField(upload_to=ruta_destino_reporte_ia, verbose_name="Archivo PDF")

    class Meta:
        ordering = ['-fecha_generacion']
        verbose_name = "Historial Reporte Dashboard IA"
        verbose_name_plural = "Historiales Reportes Dashboard IA"

    def __str__(self):
        return f"Dashboard PDF - {self.usuario.username} ({self.fecha_generacion.strftime('%d/%m/%Y %H:%M')})"
