from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from ..models import *
import os


@login_required
def acceso_manual_usuario(request):
    user = request.user
    
    rol_evaluar = request.session.get('rol_actual')
    if not rol_evaluar:
        rol_evaluar = str(getattr(user, 'rol', 'normal')).strip().lower()
    else:
        rol_evaluar = str(rol_evaluar).strip().lower()
    
    if rol_evaluar == "admin":
        return redirect('gestor_manuales_admin')

    manual = ManualSistema.objects.filter(rol=rol_evaluar).first()
    
    if manual and manual.archivo and os.path.exists(manual.archivo.path):
        return FileResponse(open(manual.archivo.path, 'rb'), content_type='application/pdf')
    
    messages.error(
        request, 
        f"El manual de usuario para el rol '{rol_evaluar}' no se encuentra disponible actualmente en el sistema."
    )
    
    next_url = request.META.get('HTTP_REFERER', 'home')
    return redirect(next_url)



@login_required
def gestor_manuales_admin(request):
    user = request.user
    
    rol_simulado = request.session.get('rol_actual')
    rol_evaluar = str(rol_simulado).strip().lower() if rol_simulado else str(getattr(user, 'rol', 'normal')).strip().lower()
    rol_real_bd = str(getattr(user, 'rol', 'normal')).strip().lower()
    
    if rol_evaluar != "admin" or rol_real_bd != "admin":
        messages.error(request, "No posees los permisos requeridos para acceder al gestor de manuales.")
        return redirect('home')

    if request.method == "POST":
        rol_seleccionado = request.POST.get("rol_manual")
        archivo_subido = request.FILES.get("archivo_pdf")

        if rol_seleccionado and archivo_subido:
            if rol_seleccionado == "jefe_gerente":
                roles_a_procesar = ["jefe", "gerente"]
            else:
                roles_a_procesar = [rol_seleccionado]

            for r in roles_a_procesar:
                manual, created = ManualSistema.objects.get_or_create(rol=r)
                if manual.archivo and os.path.exists(manual.archivo.path):
                    try:
                        os.remove(manual.archivo.path)
                    except Exception:
                        pass
                manual.archivo = archivo_subido
                manual.save()
            messages.success(request, "¡Excelente! El manual ha sido publicado y sincronizado para los roles correspondientes.")
        else:
            messages.error(request, "Formulario inválido. Asegúrese de seleccionar un rol de destino y adjuntar un archivo PDF válido.")
        
        return redirect('gestor_manuales_admin')

    manuales = ManualSistema.objects.all().order_by('rol')
    return render(request, "gestor_manuales_admin.html", {"manuales": manuales})
