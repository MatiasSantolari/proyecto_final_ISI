document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('asistenciasTableBody');
    const filterDni = document.getElementById('filterDni');
    const filterConfirmado = document.getElementById('filterConfirmado');
    const filterTardanza = document.getElementById('filterTardanza');
    const filterDepartamento = document.getElementById('filterDepartamento');
    const filterFechaDesde = document.getElementById('filterFechaDesde');
    const filterFechaHasta = document.getElementById('filterFechaHasta');
    const filterAusencia = document.getElementById('filterAusencia');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 12;
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


    
    async function loadAsistenciasData(page = 1) {
        currentPage = page; 

        const dni = filterDni.value;
        const confirmado = filterConfirmado.value;
        const tardanza = filterTardanza.value;
        const departamento_id = filterDepartamento.value;
        const fecha_desde = filterFechaDesde ? filterFechaDesde.value : '';
        const fecha_hasta = filterFechaHasta ? filterFechaHasta.value : '';
        const ausencia = filterAusencia ? filterAusencia.value : '';
        
        const apiUrl = `/api/asistencias/detalle/?dni=${dni}&confirmado=${confirmado}&tardanza=${tardanza}&departamento_id=${departamento_id}&fecha_desde=${fecha_desde}&fecha_hasta=${fecha_hasta}&ausencia=${ausencia}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar los datos de asistencia');
            
            const result = await response.json();
            
            backupData = result.results; 
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }


    function renderTable(data, isPrinting = false) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">No se encontraron registros con los filtros aplicados.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const nombreHtml = isPrinting 
                ? `<span>${item.nombre_completo}</span>` 
                : `<a href="${item.url_perfil}">${item.nombre_completo}</a>`;
            
            const esAusente = (!item.hora_entrada || item.hora_entrada === '-' || item.hora_entrada === null) && 
                              (!item.hora_salida || item.hora_salida === '-' || item.hora_salida === null);

            let horasColumnasHtml = '';
            let tardanzaHtml = '';
            
            if (esAusente) {
                horasColumnasHtml = `
                    <td colspan="2" class="text-center">
                        <span class="badge bg-danger px-3 py-1 fw-bold">Ausencia Registrada</span>
                    </td>`;
                tardanzaHtml = `<td><span class="badge bg-info">No</span></td>`;
            } else {
                const entrada = item.hora_entrada || '-';
                const salida = item.hora_salida || '-';
                horasColumnasHtml = `
                    <td>${entrada}</td>
                    <td>${salida}</td>`;
                tardanzaHtml = `<td><span class="badge bg-${item.tardanza ? 'danger' : 'info'}">${item.tardanza ? 'Sí' : 'No'}</span></td>`;
            }

            row.innerHTML = `
                <td>${nombreHtml}</td>
                <td>${item.dni}</td>
                <td>${item.departamento}</td>
                <td>${item.fecha_asistencia}</td>
                ${horasColumnasHtml}
                <td><span class="badge bg-${item.confirmado ? 'success' : 'warning'}">${item.confirmado ? 'Sí' : 'No'}</span></td>
                ${tardanzaHtml}
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
            if (pagination.has_previous) loadAsistenciasData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadAsistenciasData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadAsistenciasData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }
     
    
    filterDni.addEventListener('input', () => loadAsistenciasData(1)); 
    filterConfirmado.addEventListener('change', () => loadAsistenciasData(1));
    filterTardanza.addEventListener('change', () => loadAsistenciasData(1));
    filterDepartamento.addEventListener('change', () => loadAsistenciasData(1));
    if (filterFechaDesde) filterFechaDesde.addEventListener('change', () => loadAsistenciasData(1));
    if (filterFechaHasta) filterFechaHasta.addEventListener('change', () => loadAsistenciasData(1));
    if (filterAusencia) filterAusencia.addEventListener('change', () => loadAsistenciasData(1));


    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterConfirmado.value = '';
        filterTardanza.value = '';
        filterDepartamento.value = '';
        if (filterFechaDesde) filterFechaDesde.value = '';
        if (filterFechaHasta) filterFechaHasta.value = '';
        if (filterAusencia) filterAusencia.value = '';

        loadAsistenciasData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos correctamente.', 'info');
    });



    downloadCsvBtn.addEventListener('click', () => {
        const dni = filterDni.value;
        const confirmado = filterConfirmado.value;
        const tardanza = filterTardanza.value;
        const departamento_id = filterDepartamento.value;
        const fecha_desde = filterFechaDesde ? filterFechaDesde.value : '';
        const fecha_hasta = filterFechaHasta ? filterFechaHasta.value : '';
        const ausencia = filterAusencia ? filterAusencia.value : '';

        const exportUrl = `/api/asistencias/exportar/csv/?dni=${dni}&confirmado=${confirmado}&tardanza=${tardanza}&departamento_id=${departamento_id}&fecha_desde=${fecha_desde}&fecha_hasta=${fecha_hasta}&ausencia=${ausencia}`;
        
        window.location.href = exportUrl;
    });


    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', async () => {
            const dni = filterDni.value;
            const confirmado = filterConfirmado.value;
            const tardanza = filterTardanza.value;
            const departamento_id = filterDepartamento.value;
            const fecha_desde = filterFechaDesde ? filterFechaDesde.value : '';
            const fecha_hasta = filterFechaHasta ? filterFechaHasta.value : '';
            const ausencia = filterAusencia ? filterAusencia.value : '';

            const originalContent = downloadPdfBtn.innerHTML;
            downloadPdfBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
            downloadPdfBtn.disabled = true;

            const exportUrl = `/api/asistencias/detalle/?dni=${dni}&confirmado=${confirmado}&tardanza=${tardanza}&departamento_id=${departamento_id}&fecha_desde=${fecha_desde}&fecha_hasta=${fecha_hasta}&ausencia=${ausencia}&page=1&per_page=5000`;
            
            try {
                const response = await fetch(exportUrl);
                if (!response.ok) throw new Error('Error al recopilar el historial completo');
                const result = await response.json();
                if (paginationControls) paginationControls.innerHTML = '';
                renderTable(result.results, true);
                window.print();
            } catch (err) {
                console.error("Falló la compilación de datos para PDF:", err);
                alert("No se pudieron recopilar todos los registros filtrados para el PDF.");
            } finally {
                downloadPdfBtn.innerHTML = originalContent;
                downloadPdfBtn.disabled = false;
                renderTable(backupData, false);
                loadAsistenciasData(currentPage);
            }
        });
    }

    populateDepartamentosSelector();
    loadAsistenciasData(1);
});
