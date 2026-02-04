document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('objetivosTableBody');
    const filterTipoObjetivo = document.getElementById('filterTipoObjetivo');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 20; 

    async function loadObjetivosData(page = 1) {
        currentPage = page; 

        const tipoSeleccionado = filterTipoObjetivo.value; 
        
        let tipoParam = '';
        if (tipoSeleccionado !== 'todos') {
            tipoParam = `&tipo=${tipoSeleccionado}`; 
        }

        const apiUrl = `/api/objetivos/detalle/emp/?page=${currentPage}&per_page=${itemsPerPage}${tipoParam}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar los datos de objetivos');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }

    
    function parseISODateLocal(dateString) {
        if (!dateString) return null;
        const parts = dateString.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }


    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No se encontraron objetivos con los filtros aplicados.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const esDiario = item.fechaLimite === null || item.fechaLimite === undefined;
            const tipoTexto = esDiario ? 'Recurrente' : 'Por Cargo';
            const tipoBadgeClass = esDiario ? 'badge bg-info text-dark' : 'badge bg-primary';
            const fechaLimiteObj = parseISODateLocal(item.fechaLimite);
            const fechaAsigObj = parseISODateLocal(item.fechaAsignacion);
            const fechaDisplay = esDiario ? fechaAsigObj.toLocaleDateString() : fechaLimiteObj.toLocaleDateString();

            let estadoBadgeClass;
            switch (item.estado) {
                case 'Completado':
                    estadoBadgeClass = 'bg-success';
                    break;
                case 'Vencido':
                case 'No Completado':
                    estadoBadgeClass = 'bg-danger';
                    break;
                case 'Pendiente':
                case 'Pendiente':
                default:
                    estadoBadgeClass = 'bg-warning text-dark'; 
                    break;
            }

            row.innerHTML = `
                <td>${item.titulo}</td>
                <td>${item.descripcion}</td>
                <td>${fechaDisplay}</td>
                <td><span class="${tipoBadgeClass}">${tipoTexto}</span></td>
                <td><span class="badge ${estadoBadgeClass}">${item.estado}</span></td>
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
            if (pagination.has_previous) loadObjetivosData(pagination.current_page - 1);
        });
        paginationControls.appendChild(prevItem);

        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageItem = document.createElement('li');
            pageItem.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageItem.addEventListener('click', (e) => {
                e.preventDefault();
                loadObjetivosData(i);
            });
            paginationControls.appendChild(pageItem);
        }

        const nextItem = document.createElement('li');
        nextItem.className = `page-item ${!pagination.has_next ? 'disabled' : ''}`;
        nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next">»</a>`;
        nextItem.addEventListener('click', (e) => {
            e.preventDefault();
            if (pagination.has_next) loadObjetivosData(pagination.current_page + 1);
        });
        paginationControls.appendChild(nextItem);
    }
     
    
    filterTipoObjetivo.addEventListener('change', () => loadObjetivosData(1));

    loadObjetivosData(1);
});
