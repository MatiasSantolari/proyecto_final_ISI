document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('nominasTableBody');
    const paginationControls = document.getElementById('paginationControls');
    
    const filterDni = document.getElementById('filterDni');
    const filterEstado = document.getElementById('filterEstado');
    const filterDepartamento = document.getElementById('filterDepartamento');
    const filterFechaDesde = document.getElementById('filterFechaDesde');
    const filterFechaHasta = document.getElementById('filterFechaHasta');    
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');

    let backupData = [];

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
    const itemsPerPage = 10;
    
    async function loadNominasData(page = 1) {
        currentPage = page; 

        const dni = filterDni.value;
        const estado = filterEstado.value;
        const departamento_id = filterDepartamento.value;
        const fecha_desde = filterFechaDesde ? filterFechaDesde.value : '';
        const fecha_hasta = filterFechaHasta ? filterFechaHasta.value : '';

        const apiUrl = `/api/nominas/detalle/?dni=${dni}&estado=${estado}&departamento_id=${departamento_id}&fecha_desde=${fecha_desde}&fecha_hasta=${fecha_hasta}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl); 
            if (!response.ok) throw new Error('Error al cargar los datos de nominas');
            
            const result = await response.json();
            
            backupData = result.results;
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    function renderTable(data, isPrinting = false) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center">No se encontraron nóminas.</td></tr>`;
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            const formatCurrency = (value) => `$${value.toFixed(2)}`;
            const estadoClass = item.estado === 'pagado' ? 'success' : item.estado === 'pendiente' ? 'warning' : 'danger';
            
            const nombreHtml = isPrinting 
                ? `<span>${item.nombre_completo}</span>` 
                : `<a href="${item.url_perfil}">${item.nombre_completo}</a>`;
            
            let fechaPagoHtml;
            if (item.fecha_pago) {
                fechaPagoHtml = item.fecha_pago;
            } else {
                if (isPrinting) {
                    fechaPagoHtml = `<span class="text-muted fw-semibold" style="font-size: 0.75rem;">Pendiente de Pago</span>`;
                } else {
                    const urlConParametro = `${item.url_pago}?from_detalle=1`;
                    fechaPagoHtml = `<a href="${urlConParametro}" class="btn btn-sm btn-primary">Ir a pagar</a>`;
                }
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
        if (!pagination) return;

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
    if (filterFechaDesde) filterFechaDesde.addEventListener('change', () => loadNominasData(1));
    if (filterFechaHasta) filterFechaHasta.addEventListener('change', () => loadNominasData(1));

    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterEstado.value = '';
        filterDepartamento.value = '';
        if (filterFechaDesde) filterFechaDesde.value = '';
        if (filterFechaHasta) filterFechaHasta.value = '';

        loadNominasData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos.', 'info');
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value, 
            estado: filterEstado.value,
            departamento_id: filterDepartamento.value,
            fecha_desde: filterFechaDesde ? filterFechaDesde.value : '',
            fecha_hasta: filterFechaHasta ? filterFechaHasta.value : ''
        });
        window.location.href = `/api/nominas/exportar/csv/?${params.toString()}`;
    });

    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            const params = new URLSearchParams({
                dni: filterDni.value,
                estado: filterEstado.value,
                departamento_id: filterDepartamento.value,
                fecha_desde: filterFechaDesde ? filterFechaDesde.value : '',
                fecha_hasta: filterFechaHasta ? filterFechaHasta.value : '',
                page: 1,
                per_page: 5000 
            });

            const originalContent = downloadPdfBtn.innerHTML;
            downloadPdfBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
            downloadPdfBtn.disabled = true;
            
            try {
                const response = await fetch(`/api/nominas/detalle/?${params.toString()}`);
                if (!response.ok) throw new Error('Error al compilar listado masivo');
                const result = await response.json();

                if (paginationControls) paginationControls.innerHTML = '';

                renderTable(result.results, true);

                window.print();

            } catch (err) {
                console.error("Fallo la descarga de registros de nóminas:", err);
                alert("No se pudieron recopilar todos los registros filtrados para el PDF.");
            } finally {
                downloadPdfBtn.innerHTML = originalContent;
                downloadPdfBtn.disabled = false;
                
                renderTable(backupData, false);
                loadNominasData(currentPage);
            }
        });
    }

    populateDepartamentosSelector(); 
    loadNominasData(1);
});
