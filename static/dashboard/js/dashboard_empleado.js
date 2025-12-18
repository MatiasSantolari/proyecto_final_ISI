(() => {
    const API = {
        data: '/dashboard/api/empleado/objetivos/',
        marcar: '/dashboard/marcar-objetivo-completado/'
    };


    async function safeFetch(url) {
        try {
            const res = await fetch(url, { credentials: 'same-origin' });
            if (!res.ok) throw new Error('Error de red');
            return await res.json();
        } catch (err) {
            console.error('Fetch error:', err);
            return null;
        }
    }


    async function loadDashboard() {
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


    window.toggleObjetivo = async (id, estadoActual) => {
        const nuevoEstado = !estadoActual;
        const accion = nuevoEstado ? "completar" : "reabrir";

        if (!confirm(`¿Deseas ${accion} este objetivo?`)) {
            loadDashboard(); 
            return;
        }

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
                loadDashboard();
            } else {
                alert("Error al actualizar el objetivo.");
            }
        } catch (err) {
            console.error("Error en la petición:", err);
        }
    };


    window.marcarCompletado = async (id) => {
        if (!confirm("¿Deseas marcar esta tarea como completada?")) return;
        const res = await fetch(`${API.marcar}${id}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
        });
        if (res.ok) loadDashboard();
    };

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
