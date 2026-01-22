document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('asistenciasTableBody');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 20; 

    function parseISODateLocal(dateString) {
        if (!dateString) return null;
        const parts = dateString.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]);
    }

    async function loadAsistenciasData(page = 1) {
        currentPage = page; 

        const apiUrl = `/api/asistencias/detalle/?page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar los datos de asistencias');
            
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
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No se encontraron registros de asistencias.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const fechaAsistenciaObj = parseISODateLocal(item.fecha_asistencia);
            const fechaDisplay = fechaAsistenciaObj ? fechaAsistenciaObj.toLocaleDateString() : 'N/A';
            
            const tardanzaClass = item.tardanza ? 'bg-danger' : 'bg-success';
            const confirmadoClass = item.confirmado ? 'bg-success' : 'bg-warning text-dark';

            row.innerHTML = `
                <td>${fechaDisplay}</td>
                <td>${item.hora_entrada || 'N/A'}</td>
                <td>${item.hora_salida || 'N/A'}</td>
                <td><span class="badge ${tardanzaClass}">${item.tardanza ? 'Sí' : 'No'}</span></td>
                <td><span class="badge ${confirmadoClass}">${item.confirmado ? 'Sí' : 'No'}</span></td>
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
     
    loadAsistenciasData(1);
});
