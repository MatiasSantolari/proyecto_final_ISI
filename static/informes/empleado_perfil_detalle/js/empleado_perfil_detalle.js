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
    

    function renderPaginationControls(pagination, controlsElement, loadFunction) {
        controlsElement.innerHTML = '';
        if (pagination.total_pages <= 1) return;

        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${!pagination.has_previous ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#" aria-label="Previous">«</a>`;
        prevItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_previous) loadFunction(pagination.current_page - 1);
        });
        controlsElement.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadFunction(i);
            });
            controlsElement.appendChild(pageItem);        
        }
        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadFunction(pagination.current_page + 1);
        });
        controlsElement.appendChild(nextItem);
    }

    

    async function safeFetch(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Fetch failed:", error);
            return null;
        }
    }


    const itemsPerPage = 15;

    async function loadNominas(page = 1) {
        const url = `/api/empleado/${empleadoId}/nominas/?page=${page}&per_page=${itemsPerPage}`;
        const result = await safeFetch(url);
    
        if (!result || result.results.length === 0) return nominasBody.innerHTML = '<tr><td colspan="5">No hay nóminas registradas.</td></tr>';
        nominasBody.innerHTML = result.results.map(item => {
            const badgeClass = item.estado === 'pagado' ? 'bg-info' : 'bg-warning';
            
            return `
            <tr>
                <td>${item.fecha}</td>
                <td>$${item.neto.toFixed(2)}</td>
                <td>$${item.beneficios.toFixed(2)}</td>
                <td>$${item.descuentos.toFixed(2)}</td>
                <td><span class="badge ${badgeClass}">${item.estado}</span></td>
            </tr>`
        }).join('');
        
        renderPaginationControls(result.pagination, nominasPaginationControls, loadNominas);
    }


    async function loadEvaluaciones(page = 1) {
        const url = `/api/empleado/${empleadoId}/evaluaciones/?page=${page}&per_page=${itemsPerPage}`;
        const result = await safeFetch(url);
    
        if (!result || result.results.length === 0) return evaluacionesBody.innerHTML = '<tr><td colspan="4">No hay evaluaciones registradas.</td></tr>';
        evaluacionesBody.innerHTML = result.results.map(item => {
            let calificacionHtml;

            if (item.calificacion === 'N/A' || item.calificacion === null || item.calificacion === undefined) {
                calificacionHtml = 'Sin calificar';
            } else {
                const calificacionNum = parseFloat(item.calificacion);
                const badgeClass = calificacionNum >= 6 ? 'bg-success' : 'bg-danger';
                
                calificacionHtml = `<span class="badge ${badgeClass}">${calificacionNum.toFixed(2)}</span>`;
            }

            return `
            <tr>
                <td>${item.fecha}</td>
                <td>${item.descripcion}</td>
                <td>${calificacionHtml}</td> 
                <td><a href="${item.url_calificacion}" class="btn btn-sm btn-primary">Ver/Calificar</a></td>
            </tr>`
        }).join('');

        renderPaginationControls(result.pagination, evaluacionesPaginationControls, loadEvaluaciones);
    }

    async function loadAsistencia(page = 1) {
        const url = `/api/empleado/${empleadoId}/asistencia/?page=${page}&per_page=${itemsPerPage}`;
        const result = await safeFetch(url);

        if (!result || result.results.length === 0) return asistenciaBody.innerHTML = '<tr><td colspan="5">No hay registros de asistencia.</td></tr>';
        asistenciaBody.innerHTML = result.results.map(item => `
            <tr>
                <td>${item.fecha}</td>
                <td>${item.entrada !== 'N/A' ? item.entrada : '-'}</td>
                <td>${item.salida !== 'N/A' ? item.salida : '-'}</td>
                <td>${item.confirmado ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-danger">No</span>'}</td>
                <td>${item.tardanza ? '<span class="badge bg-warning">Sí</span>' : '<span class="badge bg-info">No</span>'}</td>
            </tr>`
        ).join('');

        renderPaginationControls(result.pagination, asistenciasPaginationControls, loadAsistencia);
    }

    async function loadVacaciones(page = 1) {
        const url = `/api/empleado/${empleadoId}/vacaciones/?page=${page}&per_page=${itemsPerPage}`;
        const result = await safeFetch(url);

        if (!result || result.results.length === 0) return vacacionesBody.innerHTML = '<tr><td colspan="5">No hay solicitudes de vacaciones.</td></tr>';
        vacacionesBody.innerHTML = result.results.map(item => {
            let badgeClass;

            if (item.estado === 'aprobado') {
                badgeClass = 'bg-success';
            } else if (item.estado === 'rechazado') {
                badgeClass = 'bg-danger';
            } else if (item.estado === 'pendiente') {
                badgeClass = 'bg-warning';
            } else if (item.estado === 'cancelado') {
                badgeClass = 'bg-secondary'; 
            } else {
                badgeClass = 'bg-info'; 
            }
            return `
            <tr>
                <td>${item.fecha_solicitud}</td>
                <td>${item.fecha_inicio}</td>
                <td>${item.fecha_fin}</td>
                <td>${item.dias} días</td>
                <td><span class="badge ${badgeClass}">${item.estado}</span></td>
            </tr>`
        }).join('');

        renderPaginationControls(result.pagination, vacacionesPaginationControls, loadVacaciones);
    }

    
    async function loadObjetivos(page = 1) {
        const tipoSeleccionado = filtroTipoObjetivo.value;
         const url = `/api/empleado/${empleadoId}/objetivos/?page=${page}&per_page=${itemsPerPage}&tipo=${tipoSeleccionado}`;
         const result = await safeFetch(url);

        if (!result || result.results.length === 0) return objetivosBody.innerHTML = '<tr><td colspan="7">No hay objetivos asignados.</td></tr>';
        objetivosBody.innerHTML = result.results.map(item => `
            <tr>
                <td>${item.titulo}</td>
                <td>${item.descripcion !== '' ? item.descripcion : '-'}</td>
                <td>${item.departamento}</td>
                <td><span class="badge bg-secondary">${item.tipo}</span></td>
                <td>${item.fecha_asignacion}</td>
                <td>${item.fecha_limite !== 'N/A' ? item.fecha_limite : '-'}</td>
                <td>${item.completado ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-warning">No</span>'}</td>
            </tr>`
        ).join('');

        renderPaginationControls(result.pagination, objetivosPaginationControls, loadObjetivos);
    }

     filtroTipoObjetivo.addEventListener('change', () => {
        loadObjetivos(1); 
    });

    
    const employeeTabs = document.getElementById('employeeTabs');
    employeeTabs.addEventListener('shown.bs.tab', event => {
        if (event.target.id === 'nominas-tab') loadNominas(1);
        else if (event.target.id === 'evaluaciones-tab') loadEvaluaciones(1);
        else if (event.target.id === 'asistencia-tab') loadAsistencia(1);
        else if (event.target.id === 'vacaciones-tab') loadVacaciones(1);
        else if (event.target.id === 'objetivos-tab') loadObjetivos(1);
    });
});
