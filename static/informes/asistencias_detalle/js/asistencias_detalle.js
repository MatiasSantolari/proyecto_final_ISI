document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('asistenciasTableBody');
    const filterDni = document.getElementById('filterDni');
    const filterConfirmado = document.getElementById('filterConfirmado');
    const filterTardanza = document.getElementById('filterTardanza');
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


    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 50;
    
    async function loadAsistenciasData(page = 1) {
        currentPage = page; 

        const dni = filterDni.value;
        const confirmado = filterConfirmado.value;
        const tardanza = filterTardanza.value;
        const departamento_id = filterDepartamento.value;

        const apiUrl = `/api/asistencias/detalle/?dni=${dni}&confirmado=${confirmado}&tardanza=${tardanza}&departamento_id=${departamento_id}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar los datos de asistencia');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }


    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">No se encontraron registros con los filtros aplicados.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.nombre_completo}</td>
                <td>${item.dni}</td>
                <td>${item.departamento}</td>
                <td>${item.fecha_asistencia}</td>
                <td>${item.hora_entrada}</td>
                <td>${item.hora_salida}</td>
                <td><span class="badge bg-${item.confirmado ? 'success' : 'warning'}">${item.confirmado ? 'Sí' : 'No'}</span></td>
                <td><span class="badge bg-${item.tardanza ? 'danger' : 'info'}">${item.tardanza ? 'Sí' : 'No'}</span></td>
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
     
    
    filterDni.addEventListener('input', loadAsistenciasData(1)); 
    filterConfirmado.addEventListener('change', loadAsistenciasData(1));
    filterTardanza.addEventListener('change', loadAsistenciasData(1));
    filterDepartamento.addEventListener('change', () => loadAsistenciasData(1));


    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterConfirmado.value = '';
        filterTardanza.value = '';
        filterDepartamento.value = '';
        loadAsistenciasData(1);
        if (typeof mostrarToast === 'function') { 
            mostrarToast('Filtros restablecidos correctamente.', 'info'); 
        } else {
            console.warn('La función mostrarToast no está disponible.');
        }
    });


    downloadCsvBtn.addEventListener('click', () => {
        const dni = filterDni.value;
        const confirmado = filterConfirmado.value;
        const tardanza = filterTardanza.value;
        const departamento_id = filterDepartamento.value;
        const exportUrl = `/api/asistencias/exportar/csv/?dni=${dni}&confirmado=${confirmado}&tardanza=${tardanza}&departamento_id=${departamento_id}`;
        
        window.location.href = exportUrl;
    });

    populateDepartamentosSelector();
    loadAsistenciasData(1);
});
