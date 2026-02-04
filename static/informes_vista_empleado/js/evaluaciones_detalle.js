document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('evaluacionesTableBody');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 15; 

     function parseISODateLocal(dateString) {
        if (!dateString) return null;
        const parts = dateString.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]); 
    }

    async function loadEvaluacionesData(page = 1) {
        currentPage = page; 

        const apiUrl = `/api/evaluaciones/detalle/emp/?page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Error al cargar los datos de evaluaciones');
            
            const result = await response.json();
            
            renderTable(result.results);
            renderPagination(result.pagination);

        } catch (error) {
            console.error(error);
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error al cargar los datos.</td></tr>`;
        }
    }


    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No se encontraron registros de evaluaciones.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const fechaRegistroObj = parseISODateLocal(item.fecha_registro);
            const fechaDisplay = fechaRegistroObj ? fechaRegistroObj.toLocaleDateString() : 'N/A';
            
            const calificacionDisplay = item.calificacion_final 
                ? `<span class="badge bg-primary fs-6">${item.calificacion_final}</span>` 
                : 'Sin Calificar';


            row.innerHTML = `
                <td>${item.descripcion || 'Sin descripción'}</td>
                <td>${fechaDisplay}</td>
                <td>${item.comentarios || ''}</td>
                <td>${calificacionDisplay}</td>
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
     
    loadEvaluacionesData(1);
});
