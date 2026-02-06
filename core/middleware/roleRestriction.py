from django.shortcuts import redirect
from django.contrib import messages

class RoleRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        rol = request.session.get('rol_actual')

        RUTAS_SOLO_GESTION = [
            '/usuarios/', '/personas/', '/cargos/', '/departamentos/', '/habilidades/', '/instituciones/', 
            '/logros/', '/postulaciones/', '/habilitar_cargo/', '/limpiar_postulaciones/', '/objetivos/', 
            '/beneficios/', '/descuentos/', '/asignador_beneficio_descuento/', '/nominas/', 
            '/asistencia/confirmar/', '/vacaciones/gestionar/', '/contratos/', '/tipos_contrato/', 
            '/tipos_criterios/', '/criterios/', '/evaluaciones/', '/dashboard/api/kpis/', '/dashboard/api/vacaciones/',
            '/dashboard/api/asistencias/', '/dashboard/api/evaluaciones/', '/dashboard/api/nominas/', 
            '/dashboard/api/costo_laboral_comp/', '/dashboard/api/estructura/', '/dashboard/api/objetivos/', 
            '/departamentos/list/', '/asistencias/detalle/', '/api/asistencias/detalle/',
            '/api/asistencias/exportar/csv/', '/empleados/detalle/', '/api/empleados/', '/api/empleado/',
            '/nominas/detalle/', '/api/nominas/', '/evaluaciones/detalle/', '/api/evaluaciones/', 
            ]
        
        RUTAS_TODOS_MENOS_NORMAL = [
            '/mis_vacaciones/', '/mis_asistencias/', '/perfil_empleado/', '/marcar_asistencia/',
            '/dashboard/api/empleado/', '/dashboard/marcar-objetivo-completado/', '/objetivos/detalle/emp/',
            '/api/objetivos/detalle/emp/','/asistencias/detalle/emp/','/api/asistencias/detalle/emp/',
            '/evaluaciones/detalle/emp/','/api/evaluaciones/detalle/emp/','/mi-panel/', '/asistencia/registrar/',
            '/mis-nominas/', '/cambiar_vista/',
        ]
        if any(request.path.startswith(ruta) for ruta in RUTAS_SOLO_GESTION):
            if rol not in ['admin', 'jefe', 'gerente']:
                return self.denegar(request)
            
        if any(path.startswith(ruta) for ruta in RUTAS_TODOS_MENOS_NORMAL):
            if rol == 'normal' or not rol:
                return self.denegar(request)

        return self.get_response(request)

    def denegar(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Acceso denegado: No tenes permisos para esta seccion.")
        return redirect('home')