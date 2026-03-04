document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('objectivesTableBody');
    const filterDni = document.getElementById('filterDni');
    const filterEstado = document.getElementById('filterEstado');
    const filterRecurrencia = document.getElementById('filterRecurrencia');
    const filterDepartamento = document.getElementById('filterDepartamento');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 12;

    async function populateDepartamentosSelector() {
        const apiUrl = '/api/departamentos/list/';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar departamentos');
            const departamentos = await response.json();
            departamentos.forEach(dep => {
                const option = new Option(dep.nombre, dep.id);
                filterDepartamento.add(option);
            });
        } catch (error) { console.error("Error deptos:", error); }
    }

    async function loadObjectivesData(page = 1) {
        currentPage = page; 
        const dni = filterDni.value;
        const completado = filterEstado.value;
        const tipo_recurrencia = filterRecurrencia.value;
        const departamento_id = filterDepartamento.value;

        const apiUrl = `/api/objetivos/detalle/?dni=${dni}&completado=${completado}&tipo_recurrencia=${tipo_recurrencia}&departamento_id=${departamento_id}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error API');
            const result = await response.json();
            renderTable(result.results);
            renderPagination(result.pagination);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-body">No se encontraron objetivos.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            const nombreHtml = `<a href="${item.url_perfil}" class="fw-bold text-decoration-none">${item.empleado}</a>`;
            
            const typeBadge = `<span class="badge bg-${item.es_recurrente ? 'info' : 'secondary'} text-white" style="font-size: 0.65rem;">${item.es_recurrente ? 'Diario' : 'Único'}</span>`;
            const statusBadge = `<span class="badge bg-${item.completado ? 'success' : 'warning'} text-dark" style="min-width: 80px;">${item.completado ? 'Listo' : 'Pendiente'}</span>`;
            
            const fechaFinHtml = item.es_recurrente 
                ? `<span class="text-body">${item.fecha_limite}</span>` 
                : `<span class="text-body">${item.fecha_limite}</span>`;

            row.innerHTML = `
                <td>${nombreHtml}</td>
                <td class="text-body">${item.dni}</td>
                <td class="text-start text-body">${item.objetivo_titulo}</td>
                <td>${typeBadge}</td>
                <td class="text-body">${item.departamento}</td>
                <td>${fechaFinHtml}</td>
                <td>${statusBadge}</td>
            `;
            tbody.appendChild(row);
        });
    }


    function renderPagination(pagination) {
        paginationControls.innerHTML = '';
        const prevItem = document.createElement('li');
        prevItem.className = `page-item ${!pagination.has_previous ? 'disabled' : ''}`;
        prevItem.innerHTML = `<a class="page-link" href="#">«</a>`;
        prevItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_previous) loadObjectivesData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadObjectivesData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadObjectivesData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }

    filterDni.addEventListener('input', () => loadObjectivesData(1)); 
    filterEstado.addEventListener('change', () => loadObjectivesData(1));
    filterRecurrencia.addEventListener('change', () => loadObjectivesData(1));
    filterDepartamento.addEventListener('change', () => loadObjectivesData(1));

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = ''; filterEstado.value = ''; filterRecurrencia.value = ''; filterDepartamento.value = '';
        loadObjectivesData(1);
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value,
            completado: filterEstado.value,
            tipo_recurrencia: filterRecurrencia.value,
            departamento_id: filterDepartamento.value
        });
        window.location.href = `/api/objetivos/exportar/csv/?${params.toString()}`;
    });

    populateDepartamentosSelector();
    loadObjectivesData(1);
});
