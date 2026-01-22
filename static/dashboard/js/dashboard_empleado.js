(() => {
    const API = {
        data: '/dashboard/api/empleado/objetivos/',
        asistencia: '/dashboard/api/empleado/asistencia/',
        evaluaciones: '/dashboard/api/empleado/evaluaciones/',
        beneficios: '/dashboard/api/empleado/beneficios/',
        logros: '/dashboard/api/empleado/logros/',
        marcar: '/dashboard/marcar-objetivo-completado/'
    };


    async function safeFetch(url, options = {}) {
        try {
            const res = await fetch(url, { credentials: 'same-origin', ...options });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({})); 
                throw new Error(errorData.error || `Error de red: ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error('Fetch error:', err);
            return null;
        }
    }


    async function loadDashboard() {
        await loadObjetivos(); 
        await loadAsistenciaCard(); 
        await loadEvaluacionesCard();
        await loadBeneficiosCard();
        await loadLogrosCard();
    }
    
    
    async function loadObjetivos() {
        const data = await safeFetch(API.data);
        if (!data) return;

        document.getElementById('displayHoy').innerText = `Hoy es ${data.fecha_formateada}`;

        const diariosCont = document.getElementById('containerDiarios');
        let realizadosDiarios = 0;

        diariosCont.innerHTML = data.diarios.length ? '' : '<div class="text-center py-4 text-muted">No hay tareas para hoy.</div>';
        
        data.diarios.forEach(item => {
            if (item.completado) realizadosDiarios++;
            
            const bgClass = item.completado ? 'bg-light opacity-75' : 'bg-dark-completed';    
            const textClasses = item.completado ? 'text-decoration-line-through text-muted' : 'text-dark';

            diariosCont.innerHTML += `
                <div class="d-flex align-items-center justify-content-between py-1 px-3 mb-2 rounded border-start border-4 border-primary shadow-sm 
                    ${bgClass}"> 
                    <div class="${textClasses}">
                        <h6 class="m-0 fw-bold">${item.titulo}</h6>
                        <small class="text-muted">${item.descripcion || ''}</small>
                    </div>
                    <div class="form-check align-self-center">
                        <input class="form-check-input h4" type="checkbox" 
                            ${item.completado ? 'checked' : ''} 
                            style="cursor: pointer;"
                            title="${item.completado ? 'Reabrir objetivo' : 'Marcar como completado'}"
                            onclick="toggleObjetivo(${item.id}, ${item.completado})">
                    </div>
                </div>`;
        });

        const porcDiario = data.diarios.length ? Math.round((realizadosDiarios / data.diarios.length) * 100) : 0;
        const barraDiaria = document.getElementById('progresoDiario');
        if(barraDiaria) {
            barraDiaria.style.width = porcDiario + '%';
            barraDiaria.innerText = porcDiario + '%';
        }


        let objetivosCargo = [...data.cargo];

        objetivosCargo.sort((a, b) => {
            if (a.completado !== b.completado) {
                return a.completado - b.completado;
            }
            
            const dateA = a.fecha_completa ? new Date(a.fecha_completa) : new Date('9999-12-31');
            const dateB = b.fecha_completa ? new Date(b.fecha_completa) : new Date('9999-12-31');
            return dateA - dateB;
        });


        const cargoCont = document.getElementById('containerCargo');
        let realizadosCargo = 0;

        cargoCont.innerHTML = data.cargo.length ? '' : '<tr><td colspan="3" class="text-center py-4 text-muted">No hay objetivos de puesto asignados.</td></tr>';

        data.cargo.forEach(item => {
            if (item.completado) realizadosCargo++;

            const filaEstilo = item.completado ? 'bg-light opacity-75' : ''; 
            
            const textoEstilo = item.completado ? 'text-muted' : 'text-dark';
           
            let badgeClass = 'bg-secondary text-white';
            let badgeIcon = '<i class="bi bi-calendar-event me-1"></i>';
            let textoBadge = item.vence ? `Fecha limite: ${item.vence}` : 'Sin fecha límite';

            if (item.completado) {
                badgeClass = 'bg-success text-white'; 
                badgeIcon = '<i class="bi bi-check-circle-fill me-1"></i>';
                textoBadge = 'Finalizado';
            } else {
                if (item.atrasado) {
                    badgeClass = 'bg-danger text-white shadow-sm';
                    badgeIcon = '<i class="bi bi-exclamation-triangle-fill me-1"></i>';
                } else if (item.es_hoy) {
                    badgeClass = 'bg-warning text-dark shadow-sm'; 
                    badgeIcon = '<i class="bi bi-hourglass-split me-1"></i>';
                    textoBadge = 'VENCE HOY';
                } else {
                    badgeClass = 'bg-info text-white'; 
                }
            }

            cargoCont.innerHTML += `
                <tr class="${filaEstilo} p-4 table-compact-goals"> 
                    <td class="${textoEstilo}">
                        <div class="fw-bold">${item.titulo}</div>
                        <small class="text-muted d-block" style="max-width: 280px;">
                            ${item.descripcion || 'Sin descripción adicional'}
                        </small>
                    </td>
                    <td style="width: 160px;">
                        <span class="badge ${badgeClass} p-2 w-100 d-flex align-items-center justify-content-center">
                            ${badgeIcon} ${textoBadge}
                        </span>
                    </td>
                    <td class="text-center" style="width: 80px;">
                        <button class="btn btn-sm ${item.completado ? 'btn-outline-secondary' : 'btn-success'} rounded-circle shadow-sm" 
                                title="${item.completado ? 'Reabrir objetivo' : 'Marcar como completado'}"
                                onclick="toggleObjetivo(${item.id}, ${item.completado})">
                            <i class="bi ${item.completado ? 'bi-arrow-counterclockwise' : 'bi-check-lg'}"></i>
                        </button>
                    </td>
                </tr>`;
        });


        const porcCargo = data.cargo.length ? Math.round((realizadosCargo / data.cargo.length) * 100) : 0;
        const barraCargo = document.getElementById('progresoCargo');
        if(barraCargo) {
            barraCargo.style.width = porcCargo + '%';
            barraCargo.innerText = porcCargo + '%';
            if(porcCargo === 100) barraCargo.classList.replace('bg-info', 'bg-success');
            else barraCargo.classList.replace('bg-success', 'bg-info');
        }
    
    }

    
    
    async function loadAsistenciaCard() {
        const cont = document.getElementById('containerAsistenciaCard');
        cont.innerHTML = '<div class="text-center text-muted py-3">Cargando...</div>';

        const dataAsistencia = await safeFetch(API.asistencia);
        
        if (!dataAsistencia) {
            cont.innerHTML = '<div class="text-center text-danger py-3">Error de carga.</div>';
            return;
        }

        const asistencia = dataAsistencia.asistencia_mes;
        const estadoHoy = dataAsistencia.estado_hoy;
        
        let recordatorioHTML = '';
        if (estadoHoy === "Nada marcado") {
            recordatorioHTML = `<div class="alert alert-danger p-2 small"><i class="bi bi-clock me-2"></i>Recuerda marcar su <strong>**entrada**</strong> hoy (Podras hacerlo en la barra superior de tu interfaz).</div>`;
        } else if (estadoHoy === "Entrada marcada") {
            recordatorioHTML = `<div class="alert alert-warning p-2 small"><i class="bi bi-clock-history me-2"></i>Recuerda marcar su <strong>**salida**</strong> al terminar el día (Podras hacerlo en la barra superior interfaz).</div>`;
        } else if (estadoHoy === "Ambos marcados") {
            recordatorioHTML = `<div class="alert alert-success p-2 small"><i class="bi bi-check-circle me-2"></i>Asistencia de hoy registrada correctamente.</div>`;
        }

        cont.innerHTML = `
            <div class="mb-3">
                <p class="mb-1 fw-semibold text-muted">Asistencia este mes</p>
                <div class="d-flex align-items-center">
                    <h4 class="text-primary fw-bolder me-3">${asistencia}%</h4>
                    <div class="progress flex-grow-1" style="height: 10px;">
                        <div class="progress-bar bg-primary" role="progressbar" style="width: ${asistencia}%" aria-valuenow="${asistencia}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
            
            <hr>
            
            ${recordatorioHTML}
        `;
    }



    async function loadEvaluacionesCard() {
        const cont = document.getElementById('containerEvaluacionesCard');
        cont.innerHTML = '<div class="text-center text-muted py-3">Cargando...</div>';
        
        const dataEvaluaciones = await safeFetch(API.evaluaciones);

        if (!dataEvaluaciones) {
            cont.innerHTML = '<div class="text-center text-danger py-3">Error de carga.</div>';
            return;
        }

        const evaluaciones = dataEvaluaciones.promedio_evaluaciones;
        const pendientes = dataEvaluaciones.pendientes;

        let htmlContent = `
            <div class="mb-1 text-center">
                <p class="mb-1 fw-semibold text-muted">Calificación promedio (último año)</p>    
                <div class="d-flex align-items-center justify-content-center">
                    <span class="text-info fw-bolder me-3 fs-4 mt-1 mb-0">
                        ${evaluaciones} / 10 
                    </span>            
                    <span class="text-warning h4 m-0 pt-1">
                        ${typeof evaluaciones === 'number' ? '⭐' : ''}
                    </span>
                </div>
            </div>
            `;
        
        if (pendientes && pendientes.length > 0) {
            let pendientesHtml = `<hr><div class="alert alert-warning shadow-sm" role="alert">
                <h6 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>Evaluaciones Pendientes</h6>
                <p>Tienes <strong>${pendientes.length}</strong> evaluación(es) pendiente(s). <strong>Comuníquese con Recursos Humanos:</strong></p>
                
                <ul class="mb-0 ps-3">`;
            pendientes.forEach(p => {
                pendientesHtml += `<li>${p.titulo} (Reg: ${p.fecha_registro})</li>`;
            });

            pendientesHtml += `</ul></div>`;
            htmlContent += pendientesHtml;
        } else {
             htmlContent += `<hr><div class="alert alert-success shadow-sm" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>
                ¡Estás al día! No tienes evaluaciones pendientes registradas.
            </div>`;
        }


        cont.innerHTML = htmlContent;
    }



    async function loadBeneficiosCard() {
        const cont = document.getElementById('containerBeneficiosCard');
        cont.innerHTML = '<div class="text-center text-muted py-3">Cargando beneficios...</div>';

        const data = await safeFetch(API.beneficios);
        
        if (!data) {
            cont.innerHTML = '<div class="text-center text-danger py-3">Error al cargar beneficios.</div>';
            return;
        }

        let htmlContent = '';

        if (data.asignados.length > 0) {
            htmlContent += `<h6>Tus beneficios actuales (${data.asignados.length}):</h6>
            <ul class="list-group mb-4">`;
            data.asignados.forEach(b => {
                const badgeFijo = b.fijo ? '<span class="badge bg-secondary ms-2">Fijo</span>' : '';
                htmlContent += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${b.descripcion} ${badgeFijo}
                    <span class="badge bg-primary rounded-pill">${b.valor}</span>
                </li>`;
            });
            htmlContent += `</ul>`;
        } else {
            htmlContent += `<div class="alert alert-info small">Aún no tienes beneficios asignados.</div>`;
        }

        if (data.potenciales.length > 0) {
            htmlContent += `<h6 class="mt-4">Beneficios a los que puedes acceder (${data.potenciales.length}):</h6>
            <ul class="list-group">`;
            data.potenciales.forEach(b => {
                htmlContent += `<li class="list-group-item d-flex justify-content-between align-items-center list-group-item-action">
                    ${b.descripcion}
                    <span class="badge bg-success rounded-pill">${b.valor}</span>
                </li>`;
            });
            htmlContent += `</ul>`;
        } else if (data.asignados.length > 0) {
             htmlContent += `<div class="alert alert-success mt-4 small">¡Ya cuentas con todos los beneficios disponibles!</div>`;
        }

        cont.innerHTML = htmlContent;
    }



     async function loadLogrosCard() {
        const cont = document.getElementById('containerLogrosCard');
        cont.innerHTML = '<div class="text-center text-muted py-3">Cargando logros...</div>';

        const data = await safeFetch(API.logros);
        
        if (!data) {
            cont.innerHTML = '<div class="text-center text-danger py-3">Error al cargar logros.</div>';
            return;
        }

        if (data.logros.length === 0) {
            cont.innerHTML = '<div class="alert alert-info m-0">Aún no tienes logros activos o pendientes.</div>';
            return;
        }

        let htmlContent = `<div class="list-group">`;

        data.logros.forEach(logro => {
            const estadoClass = logro.completado ? 'list-group-item-success text-dark' : 'list-group-item-light text-muted';
            const iconClass = logro.completado ? 'bi-check-circle-fill text-success' : 'bi-award text-secondary opacity-50';
            const iconBadgeClass = logro.completado ? 'bg-success' : 'bg-light border';

            htmlContent += `
                <div class="list-group-item d-flex align-items-center justify-content-between ${estadoClass}">
                    <div class="d-flex align-items-center">
                        <span class="badge ${iconBadgeClass} rounded-pill p-2 me-3">
                            <i class="bi ${iconClass} h5 m-0"></i>
                        </span>
                        <div>
                            <p class="mb-0 fw-bold">${logro.titulo}</p>
                            <small class="text-muted d-block" title="Requisito">${logro.requisito}</small>
                        </div>
                    </div>
                    ${logro.completado ? `<span class="badge bg-success">Completado</span>` : `<span class="badge alert-warning text-dark">Pendiente</span>`}
                </div>
            `;
        });
        htmlContent += `</div>`;
        cont.innerHTML = htmlContent;
    }



    window.toggleObjetivo = async (id, estadoActual) => {
        const nuevoEstado = !estadoActual;
        const accion = nuevoEstado ? "completar" : "reabrir";

        try {
            const res = await fetch(`${API.marcar}${id}/`, {
                method: 'POST',
                headers: { 
                    'X-CSRFToken': getCookie('csrftoken'), 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({ completado: nuevoEstado })
            });

            if (res.ok) {
                setTimeout(() => {
                    loadDashboard(); 
                }, 150);     
            } else {
                alert("Error al actualizar el objetivo.");
                loadDashboard();
            }
        } catch (err) {
            console.error("Error en la petición:", err);
            loadDashboard();
        }
    };


    window.marcarCompletado = window.toggleObjetivo; 


    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    document.addEventListener('DOMContentLoaded', loadDashboard);
})();
