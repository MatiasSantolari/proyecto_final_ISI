import json
import io
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from xhtml2pdf import pisa
from django.shortcuts import render

from .hr_reporter import generar_informe_ia
from ...models import ReporteDashboardIA  


@login_required
@csrf_protect
@require_POST
def api_generar_reporte_ia_view(request):
    try:
        datos_dashboard = json.loads(request.body)
        rol_actual = request.session.get('rol_actual', request.user.rol)
        tipo_informe = request.GET.get('tipo', 'Diagnóstico Global de Dashboard')

        html_reporte = generar_informe_ia(
            datos=datos_dashboard, 
            rol_actual=rol_actual, 
            tipo_informe=tipo_informe
        )
        
        if "alert-danger" in html_reporte:
            return JsonResponse({"reporte": html_reporte})

        html_completo_pdf = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Helvetica, Arial, sans-serif; color: #333; font-size: 12px; line-height: 1.5; }}
                h4 {{ color: #0d6efd; font-size: 15px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; margin-top: 18px; }}
                strong {{ color: #111; }}
                ul, ol {{ margin-left: 20px; padding-left: 0; }}
                li {{ margin-bottom: 5px; }}
                .alert {{ padding: 10px; margin-bottom: 12px; border-radius: 4px; border-left: 4px solid #fff; background-color: #f8f9fa; }}
                .alert-warning {{ background-color: #fff3cd; border-color: #ffc107; color: #664d03; }}
                .alert-danger {{ background-color: #f8d7da; border-color: #dc3545; color: #842029; }}
            </style>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="margin-bottom: 2px;">{tipo_informe}</h2>
                <p style="color: #6c757d; font-size: 11px; margin-top: 0;">Generado por {request.user.username} el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            {html_reporte}
        </body>
        </html>
        """

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_completo_pdf), dest=pdf_buffer)
        
        if not pisa_status.err:
            fecha_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
            nombre_final_pdf = f"Reporte_Dashboard_{fecha_str}.pdf"

            registro_reporte = ReporteDashboardIA(usuario=request.user)
            pdf_buffer.seek(0)
            registro_reporte.archivo_pdf.save(nombre_final_pdf, ContentFile(pdf_buffer.read()), save=True)

        return JsonResponse({"reporte": html_reporte})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def api_ultimo_pdf_ia_view(request):
    """
    🌟 VISTA EXTRA: Busca el último PDF generado por el usuario conectado
    y devuelve su URL para que el JS lo descargue directo.
    """
    ultimo_reporte = ReporteDashboardIA.objects.filter(usuario=request.user).order_by('-fecha_generacion').first()
    if ultimo_reporte and ultimo_reporte.archivo_pdf:
        return JsonResponse({"url_pdf": ultimo_reporte.archivo_pdf.url})
    return JsonResponse({"url_pdf": None})




@login_required
def historial_reportes_ia_view(request):
    """
    Renderiza la tabla histórica con todos los PDFs guardados en disco,
    aplicando reglas de privacidad según el rol del usuario conectado.
    """
    rol_actual = request.session.get('rol_actual', request.user.rol)
    
    if rol_actual in ['jefe', 'gerente']:
        reportes = ReporteDashboardIA.objects.filter(usuario=request.user).order_by('-fecha_generacion')
    else:
        reportes = ReporteDashboardIA.objects.all().select_related('usuario').order_by('-fecha_generacion')
        
    return render(request, 'informes/historial_reportes_ia.html', {'reportes': reportes})
