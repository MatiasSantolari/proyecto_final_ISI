from django.db import models
from .beneficio import Beneficio
from .logro import Logro

class LogroBeneficio(models.Model):
    logro = models.ForeignKey(Logro, on_delete=models.CASCADE)
    beneficio = models.ForeignKey(Beneficio, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'LogroBeneficio'
        verbose_name_plural = 'LogrosBeneficios'
        db_table = "logro_beneficio"

    def __str__(self):
        return f"{self.logro} - {self.beneficio}"
