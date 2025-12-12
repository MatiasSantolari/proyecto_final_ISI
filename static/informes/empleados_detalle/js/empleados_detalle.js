document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('empleadosTableBody');
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

    async function loadEmpleadosData(page = 1) {
        currentPage = page; 
        
        const dni = filterDni.value;
        const estado = filterEstado.value;
        const departamento_id = filterDepartamento.value;
        
        const apiUrl = `/api/empleados/detalle/?dni=${dni}&estado=${estado}&departamento_id=${departamento_id}&page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl); 
            if (!response.ok) throw new Error('Error al cargar los datos de empleados');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }


    function renderTable(data) {

        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">No se encontraron empleados.</td></tr>`;
            return;
        }
        data.forEach(item => {
            const row = document.createElement('tr');
            const nombreHtml = `<a href="${item.url_perfil}">${item.nombre_completo}</a>`;
            row.innerHTML = `
                <td>${nombreHtml}</td>
                <td>${item.dni}</td>
                <td><span class="badge bg-info">${item.estado}</span></td>
                <td>${item.departamento}</td>
                <td>${item.cargo}</td>
                <td>${item.fecha_ingreso}</td>
                <td>${item.dias_vacaciones}</td>
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
            if (pagination.has_previous) loadEmpleadosData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadEmpleadosData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadEmpleadosData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }


    filterDni.addEventListener('input', () => loadEmpleadosData(1)); 
    filterEstado.addEventListener('change', () => loadEmpleadosData(1));
    filterDepartamento.addEventListener('change', () => loadEmpleadosData(1));
   
    clearFiltersBtn.addEventListener('click', () => {
        filterDni.value = '';
        filterEstado.value = '';
        filterDepartamento.value = '';
        loadEmpleadosData(1);
        if (typeof mostrarToast === 'function') mostrarToast('Filtros restablecidos.', 'info');
    });

    downloadCsvBtn.addEventListener('click', () => {
        const params = new URLSearchParams({
            dni: filterDni.value, estado: filterEstado.value,
            departamento_id: filterDepartamento.value
        });
        window.location.href = `/api/empleados/exportar/csv/?${params.toString()}`;
    });

    populateDepartamentosSelector();
    loadEmpleadosData(1);
});
