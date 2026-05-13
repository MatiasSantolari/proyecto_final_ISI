document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('evaluacionesTableBody');
    const paginationControls = document.getElementById('paginationControls');
    
    const filterDni = document.getElementById('filterDni');
    const filterEvaluacion = document.getElementById('filterEvaluacion');
    const filterFechaDesde = document.getElementById('filterFechaDesde');
    const filterFechaHasta = document.getElementById('filterFechaHasta');
    
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');

    let backupData = [];
    let currentPage = 1;
    const itemsPerPage = 10;

    async function populateEvaluacionesSelector() {
        const apiUrl = '/api/evaluaciones/list/';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar evaluaciones');
            const evaluaciones = await response.json();

            evaluaciones.forEach(evaluacion => {
                const option = document.createElement('option');
                option.value = evaluacion.id;
                option.textContent = evaluacion.nombre;
                filterEvaluacion.appendChild(option);
            });
        } catch (error) {
            console.error("No se pudieron cargar las evaluaciones:", error);
        }
    }

    async function loadEvaluacionesData(page = 1) {
        currentPage = page; 
        
        const params = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage,
            dni: filterDni.value,
            evaluacion_id: filterEvaluacion.value,
            fecha_desde: filterFechaDesde ? filterFechaDesde.value : '',
            fecha_hasta: filterFechaHasta ? filterFechaHasta.value : ''
        });

        const apiUrl = `/api/evaluaciones/detalle/?${params.toString()}`;

        try {
            const response = await fetch(apiUrl); 
            if (!response.ok) throw new Error('Error al cargar los datos de evaluaciones');
            
            const result = await response.json();
            
            backupData = result.results;
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    function renderTable(data, isPrinting = false) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No se encontraron evaluaciones.</td></tr>`;
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            
            const nombreHtml = isPrinting 
                ? `<span>${item.nombre_completo}</span>` 
                : `<a href="${item.url_perfil}">${item.nombre_completo}</a>`;
            
            let calificacionHtml;
            if (item.calificacion_final === 'Sin Calificar') {
                if (isPrinting) {
                    calificacionHtml = `<span class="badge bg-warning text-dark fw-bold">Sin Calificar</span>`;
                } else {
                    const url = `/evaluaciones/${item.evaluacion_id}/empleados/`;
                    calificacionHtml = `<a href="${url}" class="btn btn-sm btn-warning fw-bold">Sin Calificar</a>`;
                }
            } else {
                if (item.calificacion_final >= 6){
                    calificacionHtml = `<span class="badge bg-success">${item.calificacion_final}</span>`;
                } else {
                    calificacionHtml = `<span class="badge bg-danger">${item.calificacion_final}</span>`;
                }
            }
            row.innerHTML = `
                <td>${nombreHtml}</td>
                <td>${item.dni}</td>
                <td>${item.descripcion_evaluacion}</td>
                <td>${item.fecha_registro}</td>
                <td>${calificacionHtml}</td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderPagination(pagination) {
        paginationControls.innerHTML = '';
        if (!pagination) return;

        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${!pagination.has_previous ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#" aria-label="Previous">«</a>`;
        prevItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_previous) loadEvaluacionesData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadEvaluacionesData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadEvaluacionesData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }

    filterDni.addEventListener('input', () => loadEvaluacionesData(1)); 
    filterEvaluacion.addEventListener('change', () => loadEvaluacionesData(1));
    if (filterFechaDesde) filterFechaDesde.addEventListener('change', () => loadEvaluacionesData(1));
    if (filterFechaHasta) filterFechaHasta.addEventListener('change', () => loadEvaluacionesData(1));

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterEvaluacion.value = '';
        if (filterFechaDesde) filterFechaDesde.value = '';
        if (filterFechaHasta) filterFechaHasta.value = '';

        loadEvaluacionesData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos.', 'info');
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value,
            evaluacion_id: filterEvaluacion.value,
            fecha_desde: filterFechaDesde ? filterFechaDesde.value : '',
            fecha_hasta: filterFechaHasta ? filterFechaHasta.value : ''
        });
        window.location.href = `/api/evaluaciones/exportar/csv/?${params.toString()}`;
    });

    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            const params = new URLSearchParams({
                dni: filterDni.value,
                evaluacion_id: filterEvaluacion.value,
                fecha_desde: filterFechaDesde ? filterFechaDesde.value : '',
                fecha_hasta: filterFechaHasta ? filterFechaHasta.value : '',
                page: 1,
                per_page: 5000 
            });

            const originalContent = downloadPdfBtn.innerHTML;
            downloadPdfBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
            downloadPdfBtn.disabled = true;
            
            try {
                const response = await fetch(`/api/evaluaciones/detalle/?${params.toString()}`);
                if (!response.ok) throw new Error('Error al compilar listado masivo');
                const result = await response.json();

                if (paginationControls) paginationControls.innerHTML = '';

                renderTable(result.results, true);
                window.print();

            } catch (err) {
                console.error("Fallo la descarga de registros de evaluaciones:", err);
                alert("No se pudieron recopilar todos los registros filtrados para el PDF.");
            } finally {
                downloadPdfBtn.innerHTML = originalContent;
                downloadPdfBtn.disabled = false;
                
                renderTable(backupData, false);
                loadEvaluacionesData(currentPage);
            }
        });
    }

    populateEvaluacionesSelector(); 
    loadEvaluacionesData(1);
});
