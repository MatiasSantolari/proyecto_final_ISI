from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *


def obtener_promedio_por_departamento():
    # 1. Subquery: obtener el cargo activo del empleado
    cargo_activo = EmpleadoCargo.objects.filter(
        empleado=OuterRef("empleado"),
        fecha_fin__isnull=True
    ).order_by("-fecha_inicio").values("cargo")[:1]

    # 2. Subquery: obtener el departamento basado en ese cargo
    departamento_activo = CargoDepartamento.objects.filter(
        cargo=Subquery(cargo_activo)
    ).values("departamento__nombre")[:1]

    # 3. Query principal
    queryset = (
        EvaluacionEmpleado.objects
        .annotate(
            departamento=Subquery(departamento_activo)
        )
        .values("departamento")
        .annotate(promedio=Avg("calificacion_final"))
        .order_by("departamento")
    )

    return queryset

def reporte_evaluacion_desempeño(request):
    evaluaciones = (
        EvaluacionEmpleado.objects
        .select_related("empleado")            
        .order_by("fecha_registro")
    )
    promedios = obtener_promedio_por_departamento()

    return render(request, "reporte_evaluacion_desempeno.html", {
        "evaluaciones": evaluaciones,
        "promedios_por_area": list(promedios),
    })


