document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('capacitacionesTableBody');
    const paginationControls = document.getElementById('paginationControls');
    
    const filterDni = document.getElementById('filterDni');
    const filterCurso = document.getElementById('filterCurso');
    const filterTipo = document.getElementById('filterTipo');
    const filterEstado = document.getElementById('filterEstado');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');

    async function populateCursosSelector() {
        try {
            const response = await fetch('/api/capacitaciones/list/');
            const cursos = await response.json();
            cursos.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.nombre;
                filterCurso.appendChild(opt);
            });
        } catch (error) { console.error("Error cargando cursos:", error); }
    }

    let currentPage = 1;

    async function loadCapacitacionesData(page = 1) {
        currentPage = page;
        const params = new URLSearchParams({
            page: currentPage,
            dni: filterDni.value,
            curso_id: filterCurso.value,
            tipo: filterTipo.value,
            estado: filterEstado.value
        });

        try {
            const response = await fetch(`/api/capacitaciones/detalle/?${params.toString()}`);
            const result = await response.json();
            renderTable(result.results);
            renderPagination(result.pagination);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-danger text-center">Error al cargar datos</td></tr>`;
        }
    }

    function renderTable(data) {
        tbody.innerHTML = '';
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">No hay registros con estos filtros.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            let estadoTexto = item.estado;
            if (item.estado_raw === 'INSCRIPTO') {
                estadoTexto = item.es_externo ? 'Interesado' : 'Inscripto';
            }

            let badgeClass = 'bg-secondary';
            if(item.estado_raw === 'COMPLETADO') badgeClass = 'bg-success';
            if(item.estado_raw === 'EN_CURSO') badgeClass = 'bg-warning text-dark';
            if(item.estado_raw === 'CANCELADO') badgeClass = 'bg-danger';

            const tipoBadge = item.es_externo 
                ? '<span class="badge bg-dark text-white border">Externa</span>' 
                : '<span class="badge bg-info text-dark">Interna</span>';

            row.innerHTML = `
                <td><a href="${item.url_perfil}" class="fw-bold">${item.nombre_completo}</a></td>
                <td>${item.dni}</td>
                <td><small>${item.curso_nombre}</small></td>
                <td>${tipoBadge}</td>
                <td><span class="badge ${badgeClass}">${estadoTexto}</span></td>
                <td>${item.fecha_inscripcion}</td>
                <td>${item.tiene_certificado ? '<i class="bi bi-patch-check-fill text-success" title="Certificado cargado"></i>' : '-'}</td>
            `;
            tbody.appendChild(row);
        });

    }

    function renderPagination(pagination) {
        paginationControls.innerHTML = '';

        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${!pagination.has_previous ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#" aria-label="Previous">«</a>`;
        prevItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_previous) loadCapacitacionesData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadCapacitacionesData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadCapacitacionesData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    
    }

    // --- Eventos ---
    [filterDni, filterCurso, filterTipo, filterEstado].forEach(el => {
        el.addEventListener('change', () => loadCapacitacionesData(1));
    });
    filterDni.addEventListener('input', () => loadCapacitacionesData(1));

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = ''; filterCurso.value = ''; filterTipo.value = ''; filterEstado.value = '';
        loadCapacitacionesData(1);
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({ dni: filterDni.value, curso_id: filterCurso.value, tipo: filterTipo.value, estado: filterEstado.value });
        window.location.href = `/api/capacitaciones/exportar/csv/?${params.toString()}`;
    });

    populateCursosSelector();
    loadCapacitacionesData(1);
});
