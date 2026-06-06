document.addEventListener('DOMContentLoaded', () => {
    const empleadoId = document.getElementById('empleadoId').value;
    const nominasBody = document.getElementById('nominasBody');
    const evaluacionesBody = document.getElementById('evaluacionesBody');
    const asistenciaBody = document.getElementById('asistenciaBody');
    const vacacionesBody = document.getElementById('vacacionesBody');
    const objetivosBody = document.getElementById('objetivosBody');
    const filtroTipoObjetivo = document.getElementById('filtroTipoObjetivo');
    
    const nominasPaginationControls = document.getElementById('nominasPaginationControls');
    const evaluacionesPaginationControls = document.getElementById('evaluacionesPaginationControls');
    const asistenciasPaginationControls = document.getElementById('asistenciasPaginationControls');
    const vacacionesPaginationControls = document.getElementById('vacacionesPaginationControls');
    const objetivosPaginationControls = document.getElementById('objetivosPaginationControls');
    
    const itemsPerPage = 10;

    function renderPaginationControls(pagination, controlsElement, loadFunction) {
        controlsElement.innerHTML = '';
        if (!pagination || pagination.total_pages <= 1) return;

 
        const prevItem = document.createElement('li');
        prevItem.className = 'page-item ' + (!pagination.has_previous ? 'disabled' : '');
        prevItem.innerHTML = '<a class="page-link" href="#" aria-label="Previous">«</a>';
        prevItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_previous) loadFunction(pagination.current_page - 1);
        });
        controlsElement.appendChild(prevItem);


        const paginasAIterar = pagination.rango_paginas || [];
        paginasAIterar.forEach(num => {
            const pageItem = document.createElement('li');
            
            if (num === '…' || num === '...') {
                pageItem.className = 'page-item disabled';
                pageItem.innerHTML = '<span class="page-link" style="background: transparent; border: none; opacity: 0.65;">...</span>';
            } else {
                pageItem.className = 'page-item ' + (num === pagination.current_page ? 'active' : '');
                pageItem.innerHTML = '<a class="page-link" href="#">' + num + '</a>';
                
                pageItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (num !== pagination.current_page) {
                        loadFunction(num);
                    }
                });
            }
            controlsElement.appendChild(pageItem);        
        });


        const nextItem = document.createElement('li');
        nextItem.className = 'page-item ' + (!pagination.has_next ? 'disabled' : '');
        nextItem.innerHTML = '<a class="page-link" href="#" aria-label="Next">»</a>';
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadFunction(pagination.current_page + 1);
        });
        controlsElement.appendChild(nextItem);
    }


    async function safeFetch(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('HTTP error! status: ' + response.status);
            return await response.json();
        } catch (error) {
            console.error("Fetch failed:", error);
            return null;
        }
    }

    async function loadNominas(page = 1) {
        const url = '/api/empleado/' + empleadoId + '/nominas/?page=' + page + '&per_page=' + itemsPerPage;
        const result = await safeFetch(url);
    
        if (!result || result.results.length === 0) return nominasBody.innerHTML = '<tr><td colspan="5">No hay nóminas registradas.</td></tr>';
        nominasBody.innerHTML = result.results.map(item => {
            const badgeClass = item.estado === 'pagado' ? 'bg-info' : 'bg-warning';
            return '<tr>' +
                '<td>' + item.fecha + '</td>' +
                '<td>$' + item.neto.toFixed(2) + '</td>' +
                '<td>$' + item.beneficios.toFixed(2) + '</td>' +
                '<td>$' + item.descuentos.toFixed(2) + '</td>' +
                '<td><span class="badge ' + badgeClass + '">' + item.estado + '</span></td>' +
            '</tr>';
        }).join('');
        
        renderPaginationControls(result.pagination, nominasPaginationControls, loadNominas);
    }

    async function loadEvaluaciones(page = 1) {
        const url = '/api/empleado/' + empleadoId + '/evaluaciones/?page=' + page + '&per_page=' + itemsPerPage;
        const result = await safeFetch(url);
    
        if (!result || result.results.length === 0) return evaluacionesBody.innerHTML = '<tr><td colspan="4">No hay evaluaciones registradas.</td></tr>';
        evaluacionesBody.innerHTML = result.results.map(item => {
            let calificacionHtml;
            if (item.calificacion === 'N/A' || item.calificacion === null || item.calificacion === undefined) {
                calificacionHtml = 'Sin calificar';
            } else {
                const calificacionNum = parseFloat(item.calificacion);
                const badgeClass = calificacionNum >= 6 ? 'bg-success' : 'bg-danger';
                calificacionHtml = '<span class="badge ' + badgeClass + '">' + calificacionNum.toFixed(2) + '</span>';
            }
            return '<tr>' +
                '<td>' + item.fecha + '</td>' +
                '<td>' + item.descripcion + '</td>' +
                '<td>' + calificacionHtml + '</td> ' +
                '<td><a href="' + item.url_calificacion + '" class="btn btn-sm btn-primary">Ver/Calificar</a></td>' +
            '</tr>';
        }).join('');

        renderPaginationControls(result.pagination, evaluacionesPaginationControls, loadEvaluaciones);
    }
    
    async function loadAsistencia(page = 1) {
        const url = '/api/empleado/' + empleadoId + '/asistencia/?page=' + page + '&per_page=' + itemsPerPage;
        const result = await safeFetch(url);

        if (!result || result.results.length === 0) return asistenciaBody.innerHTML = '<tr><td colspan="5">No hay registros de asistencia.</td></tr>';
        
        asistenciaBody.innerHTML = result.results.map(item => {
            if (item.es_licencia === true) {
                return '<tr>' +
                        '<td>' + item.fecha + '</td>' +
                        '<td colspan="2" class="text-center">' +
                            '<span class="badge bg-secondary px-3 py-1 fw-semibold text-white">Licencia Justificada</span>' +
                        '</td>' +
                        '<td><span class="badge bg-success">Sí</span></td>' +
                        '<td><span class="text-muted small">—</span></td>' +
                    '</tr>';
            } else {
                const entrada = item.entrada !== 'N/A' ? item.entrada : '-';
                const salida = item.salida !== 'N/A' ? item.salida : '-';
                const confBadge = item.confirmado ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-danger">No</span>';
                const tardBadge = (item.target || item.tardanza) ? '<span class="badge bg-warning">Sí</span>' : '<span class="badge bg-info">No</span>';
                return '<tr>' +
                        '<td>' + item.fecha + '</td>' +
                        '<td>' + entrada + '</td>' +
                        '<td>' + salida + '</td>' +
                        '<td>' + confBadge + '</td>' +
                        '<td>' + tardBadge + '</td>' +
                    '</tr>';
            }
        }).join('');

        renderPaginationControls(result.pagination, asistenciasPaginationControls, loadAsistencia);
    }

        async function loadVacaciones(page = 1) {
        const url = '/api/empleado/' + empleadoId + '/vacaciones/?page=' + page + '&per_page=' + itemsPerPage;
        const result = await safeFetch(url);

        if (!result || result.results.length === 0) return vacacionesBody.innerHTML = '<tr><td colspan="5">No hay solicitudes de vacaciones.</td></tr>';
        vacacionesBody.innerHTML = result.results.map(item => {
            let badgeClass;
            if (item.estado === 'aprobado') badgeClass = 'bg-success';
            else if (item.estado === 'rechazado') badgeClass = 'bg-danger';
            else if (item.estado === 'pendiente') badgeClass = 'bg-warning';
            else if (item.estado === 'cancelado') badgeClass = 'bg-secondary'; 
            else badgeClass = 'bg-info'; 
            
            return '<tr>' +
                '<td>' + item.fecha_solicitud + '</td>' +
                '<td>' + item.fecha_inicio + '</td>' +
                '<td>' + item.fecha_fin + '</td>' +
                '<td>' + item.dias + ' días</td>' +
                '<td><span class="badge ' + badgeClass + '">' + item.estado + '</span></td>' +
            '</tr>';
        }).join('');

        renderPaginationControls(result.pagination, vacacionesPaginationControls, loadVacaciones);
    }
    
    async function loadObjetivos(page = 1) {
        const tipoSeleccionado = filtroTipoObjetivo.value;
        const url = '/api/empleado/' + empleadoId + '/objetivos/?page=' + page + '&per_page=' + itemsPerPage + '&tipo=' + tipoSeleccionado;
        const result = await safeFetch(url);

        if (!result || result.results.length === 0) return objetivosBody.innerHTML = '<tr><td colspan="7">No hay objetivos asignados.</td></tr>';
        objetivosBody.innerHTML = result.results.map(item => {
            const desc = item.descripcion !== '' ? item.descripcion : '-';
            const limite = item.fecha_limite !== 'N/A' ? item.fecha_limite : '-';
            const compBadge = item.completado ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-warning">No</span>';
            return '<tr>' +
                '<td>' + item.titulo + '</td>' +
                '<td>' + desc + '</td>' +
                '<td>' + item.departamento + '</td>' +
                '<td><span class="badge bg-secondary">' + item.tipo + '</span></td>' +
                '<td>' + item.fecha_asignacion + '</td>' +
                '<td>' + limite + '</td>' +
                '<td>' + compBadge + '</td>' +
            '</tr>';
        }).join('');

        renderPaginationControls(result.pagination, objetivosPaginationControls, loadObjetivos);
    }

    if (filtroTipoObjetivo) {
        filtroTipoObjetivo.addEventListener('change', () => {
            loadObjetivos(1); 
        });
    }

    const employeeTabs = document.getElementById('employeeTabs');
    if (employeeTabs) {
        employeeTabs.addEventListener('shown.bs.tab', event => {
            if (event.target.id === 'nominas-tab') loadNominas(1);
            else if (event.target.id === 'evaluaciones-tab') loadEvaluaciones(1);
            else if (event.target.id === 'asistencia-tab') loadAsistencia(1);
            else if (event.target.id === 'vacaciones-tab') loadVacaciones(1);
            else if (event.target.id === 'objetivos-tab') loadObjetivos(1);
            else if (event.target.id === 'habilidades-tab') {
                console.log("Pestaña de habilidades abierta.");
            }
        });
    }
    const btnGuardarHabilidadRapida = document.getElementById('btnGuardarHabilidadRapida');
    const selectHabilidad = document.getElementById('selectHabilidad');
    const modalNombreHabilidad = document.getElementById('modalNombreHabilidad');
    const modalDescHabilidad = document.getElementById('modalDescHabilidad');
    const errorAlertaHabilidad = document.getElementById('errorAlertaHabilidad');
    
    if (btnGuardarHabilidadRapida) {
        btnGuardarHabilidadRapida.addEventListener('click', async () => {
            const nombre = modalNombreHabilidad.value.trim();
            const descripcion = modalDescHabilidad.value.trim();
            
            if (!nombre) {
                errorAlertaHabilidad.textContent = "El nombre de la habilidad es requerido.";
                errorAlertaHabilidad.classList.remove('d-none');
                return;
            }
            
            errorAlertaHabilidad.classList.add('d-none');
            
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfInput ? csrfInput.value : '';
            
            try {
                const response = await fetch('/api/habilidades/crear-rapido/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ nombre: nombre, descripcion: descripcion })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const nuevaOpcion = document.createElement('option');
                    nuevaOpcion.value = data.habilidad.id;
                    nuevaOpcion.textContent = data.habilidad.nombre;
                    nuevaOpcion.selected = true; 
                    
                    selectHabilidad.appendChild(nuevaOpcion);
                    
                    modalNombreHabilidad.value = '';
                    modalDescHabilidad.value = '';
                    
                    const modalElement = document.getElementById('modalNuevaHabilidadGlobal');
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    console.log("Catálogo actualizado. Nueva habilidad inyectada: " + data.habilidad.nombre);
                } else {
                    errorAlertaHabilidad.textContent = data.error || "Ocurrió un error inesperado.";
                    errorAlertaHabilidad.classList.remove('d-none');
                }
            } catch (err) {
                console.error("Error crítico de comunicación AJAX:", err);
                errorAlertaHabilidad.textContent = "Error al intentar conectar con el servidor.";
                errorAlertaHabilidad.classList.remove('d-none');
            }
        });
    }



    const modalEliminar = document.getElementById('modalEliminarHabilidad');
    if (modalEliminar) {
        modalEliminar.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const urlEliminar = button.getAttribute('data-url');        
            const form = document.getElementById('formEliminarHabilidad');
            if (form) {
                form.action = urlEliminar;
            }
        });
    }

    const activeTab = localStorage.getItem('selectedEmpTab');
    if (activeTab) {
        const tabTrigger = document.querySelector(`button[data-bs-target="${activeTab}"]`);
        if (tabTrigger) {
            const tab = new bootstrap.Tab(tabTrigger);
            tab.show();
        }
    }

    const tabButtons = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', (event) => {
            const targetId = event.target.getAttribute('data-bs-target');
            localStorage.setItem('selectedEmpTab', targetId);
        });
    });


});
