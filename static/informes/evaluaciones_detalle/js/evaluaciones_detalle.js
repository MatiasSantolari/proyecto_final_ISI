document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('evaluacionesTableBody');
    const paginationControls = document.getElementById('paginationControls');
    
    const filterDni = document.getElementById('filterDni');
    const filterEvaluacion = document.getElementById('filterEvaluacion');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');

    
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

    let currentPage = 1;
    const itemsPerPage = 50;

    async function loadEvaluacionesData(page = 1) {
        currentPage = page; 
        const params = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage,
            dni: filterDni.value,
            evaluacion_id: filterEvaluacion.value,
        });

        const apiUrl = `/api/evaluaciones/detalle/?${params.toString()}`;

        try {
            const response = await fetch(apiUrl); 
            if (!response.ok) throw new Error('Error al cargar los datos de evaluaciones');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No se encontraron evaluaciones.</td></tr>`;
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            let calificacionHtml;
            if (item.calificacion_final === 'Sin Calificar') {
                const url = `/evaluaciones/${item.evaluacion_id}/empleados/`;
                calificacionHtml = `<a href="${url}" class="btn btn-sm btn-warning fw-bold">Sin Calificar</a>`;
            } else {
                if (item.calificacion_final >= 6){
                    calificacionHtml = `<span class="badge bg-success">${item.calificacion_final}</span>`;
                } else {
                    calificacionHtml = `<span class="badge bg-danger">${item.calificacion_final}</span>`;
                }
            }
            row.innerHTML = `
                <td>${item.nombre_completo}</td>
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

        if (pagination.total_pages <= 1) return;

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

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterEvaluacion.value = '';
        loadEvaluacionesData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos.', 'info');
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value,
            evaluacion_id: filterEvaluacion.value
        });
        window.location.href = `/api/evaluaciones/exportar/csv/?${params.toString()}`;
    });

    populateEvaluacionesSelector(); 
    loadEvaluacionesData(1);
});
