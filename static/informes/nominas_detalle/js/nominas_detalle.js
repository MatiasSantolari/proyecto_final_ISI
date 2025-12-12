document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('nominasTableBody');
    const paginationControls = document.getElementById('paginationControls');
    
    const filterDni = document.getElementById('filterDni');
    const filterEstado = document.getElementById('filterEstado');
    const filterDepartamento = document.getElementById('filterDepartamento');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');


    async function populateDepartamentosSelector() {
        const apiUrl = '/api/departamentos/list/';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar departamentos');
            const departamentos = await response.json();

            departamentos.forEach(dep => {
                const option = document.createElement('option');
                option.value = dep.id;
                option.textContent = dep.nombre;
                filterDepartamento.appendChild(option);
            });
        } catch (error) {
            console.error("No se pudieron cargar los departamentos:", error);
        }
    }


    let currentPage = 1;
    const itemsPerPage = 50;
    
    async function loadNominasData(page = 1) {
        currentPage = page; 

        const dni = filterDni.value;
        const estado = filterEstado.value;
        const departamento_id = filterDepartamento.value;

        const apiUrl = `/api/nominas/detalle/?dni=${dni}&estado=${estado}&departamento_id=${departamento_id}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl); 
            if (!response.ok) throw new Error('Error al cargar los datos de nominas');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center">No se encontraron nóminas.</td></tr>`;
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            const formatCurrency = (value) => `$${value.toFixed(2)}`;
            const estadoClass = item.estado === 'pagado' ? 'success' : item.estado === 'pendiente' ? 'warning' : 'danger';
            const nombreHtml = `<a href="${item.url_perfil}">${item.nombre_completo}</a>`;
            let fechaPagoHtml;
            if (item.fecha_pago) {
                fechaPagoHtml = item.fecha_pago;
            } else {
                const urlConParametro = `${item.url_pago}?from_detalle=1`;
                fechaPagoHtml = `<a href="${urlConParametro}" class="btn btn-sm btn-primary">Ir a pagar</a>`;
            }
            row.innerHTML = `
                <td>${nombreHtml}</td>
                <td>${item.dni}</td>
                <td>${item.departamento}</td>
                <td>${item.cargo}</td>
                <td>${item.fecha_generacion}</td>
                <td>${fechaPagoHtml}</td>
                <td><span class="badge bg-${estadoClass}">${item.estado}</span></td>
                <td>${formatCurrency(item.total_beneficios)}</td>
                <td>${formatCurrency(item.total_descuentos)}</td>
                <td>${formatCurrency(item.monto_neto)}</td>
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
            if (pagination.has_previous) loadNominasData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadNominasData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadNominasData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }

    filterDni.addEventListener('input', () => loadNominasData(1)); 
    filterEstado.addEventListener('change', () => loadNominasData(1));
    filterDepartamento.addEventListener('change', () => loadNominasData(1));

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterEstado.value = '';
        filterDepartamento.value = '';
        loadNominasData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos.', 'info');
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value, estado: filterEstado.value,
            departamento_id: filterDepartamento.value
        });
        window.location.href = `/api/nominas/exportar/csv/?${params.toString()}`;
    });

    populateDepartamentosSelector(); 
    loadNominasData(1);
});
