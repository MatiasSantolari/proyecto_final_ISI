import json
from datetime import date
from app.settings import DEEPSEEK_API_KEY
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


model_reportes = ChatDeepSeek(
    model="deepseek-chat", 
    api_key=DEEPSEEK_API_KEY,
    temperature=0.2, 
    max_tokens=3000, 
)


REPORT_PROMPT = """
Actúas como un Consultor Estratégico Senior y Director Global de Recursos Humanos (CHRO).
Tu objetivo es analizar un conjunto de datos analíticos extraídos en tiempo real de una plataforma de RRHH y confeccionar un informe ejecutivo exhaustivo.
El usuario que solicita este informe tiene el rol de: '{rol_actual}'. Si el rol es 'jefe' o 'gerente', enfoca tus conclusiones en el rendimiento de su equipo asignado; si es administrador, asume una perspectiva macro de toda la compañía.

Parámetros de Contexto:
- Fecha de emisión: {fecha_hoy}
- Tipo de informe solicitado: {tipo_informe}

Instrucciones Críticas de Análisis:
1. Encuentra correlaciones inteligentes cruzando la información provista en el JSON. Por ejemplo: vincula si las áreas con alto ausentismo o tardanzas sufren retrasos en sus objetivos, o si las bajas calificaciones se mitigan en los meses con mayor impacto de capacitaciones.
2. Analiza los costos financieros (expresados en Pesos Argentinos - ARS) evaluando proporciones (Base vs Extras/Beneficios) considerando variables contextuales y de eficiencia, priorizando alertar sobre desvíos presupuestarios.
3. Examina si el volumen de solicitudes de vacaciones pendientes denota un cuello de botella administrativo.
4. REGLA ESTRICTA DE ASOCIACIÓN DE FECHAS: Al procesar los arreglos cronológicos del módulo de 'asistencias' y 'capacitaciones', debes emparejar estrictamente cada índice del array 'labels' con el mismo índice exacto de los arrays numéricos correspondientes ('present', 'late', 'ausent', 'internas', 'externas'). Si una etiqueta de fecha tiene asignado el valor 0 en el array de ausencias o registros, significa que NO HUBO incidencias en ese periodo. Está prohibido alucinar, asumir o inventar ausencias o métricas en meses donde el dato numérico real entregado sea cero.

Reglas Estrictas de Formato, Contraste y Estilo Minimalista (MANDATORIAS):
1. Responde EXCLUSIVAMENTE utilizando código HTML válido y limpio listo para insertar (utiliza etiquetas como <h4>, <p>, <ul>, <li>, <strong>).
2. Está TERMINANTEMENTE PROHIBIDO usar bloques de código markdown tradicionales (como ```html) o incluir etiquetas de documentos globales (<html>, <head>, <body>).
3. PROHIBICIÓN DE COLORES Y FONDOS SÓLIDOS: Está totalmente prohibido inyectar estilos inline de color o usar clases de Bootstrap que pinten fondos de cajas enteros (PROHIBIDO usar 'bg-light', 'bg-white', 'bg-warning', 'bg-opacity-*' o la clase 'card'). Buscamos un diseño plano, moderno, limpio y de alta gama.
4. ESTRUCTURA OBLIGATORIA POR BLOQUES (LINE DESIGN): Para que el informe sea escaneable y no sea un bloque de texto plano aburrido, debes empaquetar CADA hallazgo o alerta dentro de la siguiente estructura exacta de líneas laterales finas:
   - Para los Títulos principales de las secciones: Usa etiquetas <h4> con las clases 'fw-bold text-primary mb-3 mt-4'.
   - Cada Alerta de Advertencia/Hallazgo intermedio (Amarillo): Debe ir envuelta OBLIGATORIAMENTE en un div con esta clase:
     <div class="ps-3 mb-3 border-start border-2 border-warning">
       <span class="fw-bold text-warning"><i class="bi bi-exclamation-triangle-fill"></i> Alerta de Rendimiento:</span> 
       <p class="text-body d-inline">Aquí pones tu análisis redactado en un párrafo...</p>
     </div>
   - Cada Alerta Crítica/Desvío (Rojo): Debe ir envuelta OBLIGATORIAMENTE en un div con esta clase:
     <div class="ps-3 mb-3 border-start border-2 border-danger">
       <span class="fw-bold text-danger"><i class="bi bi-shield-fill-x"></i> Desvío Crítico:</span> 
       <p class="text-body d-inline">Aquí pones tu análisis redactado en un párrafo...</p>
     </div>
5. Cada vez que abras un párrafo común fuera de las alertas, usa <p class="text-body mb-3">. Para las listas de acciones finales, utiliza <ul> y <li> con la clase 'mb-2 text-body'.
6. Sé directo, asertivo y prescriptivo: mantén esta misma riqueza de datos del análisis económico argentino y las metas, pero estructurado con los bloques visuales anteriores.

Datos a procesar:
{datos_json}
"""



prompt_template = ChatPromptTemplate.from_template(REPORT_PROMPT)

chain_informes = prompt_template | model_reportes | StrOutputParser()

def generar_informe_ia(datos: dict, rol_actual: str, tipo_informe: str) -> str:
    """
    Función de entrada para tu backend de Django. 
    Procesa cualquier estructura JSON y retorna el reporte HTML limpio.
    """
    try:
        resultado_html = chain_informes.invoke({
            "rol_actual": rol_actual,
            "fecha_hoy": date.today().strftime('%Y-%m-%d'),
            "tipo_informe": tipo_informe,
            "datos_json": json.dumps(datos, ensure_ascii=False)
        })
        return resultado_html
    except Exception as e:
        return f"""
        <div class="alert alert-danger d-flex align-items-center gap-2 m-0 border-0 shadow-sm">
          <i class="bi bi-exclamation-triangle-fill"></i>
          <div>
            <strong>Error del Consultor de IA:</strong> No pudimos conectar con el motor analítico de DeepSeek. Por favor, reintenta la operación.
          </div>
        </div>
        """
