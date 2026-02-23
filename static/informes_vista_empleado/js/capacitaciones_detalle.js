document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.getElementById('capacitacionesTableBody');
    const paginationControls = document.getElementById('paginationControls');

    let currentPage = 1;
    const itemsPerPage = 15; 

    function parseISODateLocal(dateString) {
        if (!dateString) return null;
        const parts = dateString.split('-');
        return new Date(parts[0], parts[1] - 1, parts[2]); 
    }

    async function loadCapacitacionesData(page = 1) {
        currentPage = page; 
        const apiUrl = `/api/capacitaciones/detalle/emp/?page=${currentPage}&per_page=${itemsPerPage}`;

        try {
            const response = await fetch(apiUrl);
            const result = await response.json();
            renderTable(result.results);
            renderPagination(result.pagination);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error al cargar datos.</td></tr>`;
        }
    }


    
    function renderTable(data) {
        tbody.innerHTML = ''; 
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-3">No hay registros.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const row = document.createElement('tr');
            
            const fInicioObj = parseISODateLocal(item.fecha_inicio);
            const inicioDisplay = fInicioObj ? 
                fInicioObj.toLocaleDateString() : 
                `<span class="text-info small"><i class="bi bi-clock-history me-1"></i>A tu ritmo</span>`;

            const fInscObj = parseISODateLocal(item.fecha_inscripcion);
            const fFinObj = parseISODateLocal(item.fecha_completado);

            let estadoTexto = item.estado; 
            let badgeClass = 'bg-secondary text-white';

            if (item.estado_raw === 'INSCRIPTO') {
                if (item.es_externo) {
                    estadoTexto = "Interesado";
                    badgeClass = 'bg-info text-dark shadow-sm'; 
                } else {
                    estadoTexto = "Inscripto";
                    badgeClass = 'bg-primary text-white shadow-sm';
                }
            } else if (item.estado_raw === 'COMPLETADO') {
                badgeClass = 'bg-success text-white';
            } else if (item.estado_raw === 'EN_CURSO') {
                badgeClass = 'bg-warning text-dark';
            } else if (item.estado_raw === 'CANCELADO') {
                badgeClass = 'bg-danger text-white';
            }

            const tipoBadge = item.es_externo ? 
                `<span class="badge border border-info text-info">Externo</span>` : 
                `<span class="badge border border-success text-success">Interno</span>`;

            let accionHtml = '-';
            if (item.es_externo && item.url_curso) {
                accionHtml = `<a href="${item.url_curso}" target="_blank" class="btn btn-xs btn-outline-primary py-0 px-2 shadow-sm">
                                <i class="bi bi-box-arrow-up-right"></i> Ir</a>`;
            }

            row.innerHTML = `
                <td class="text-start ps-3 fw-bold">${item.curso}</td>
                <td>${tipoBadge}</td>
                <td>${inicioDisplay}</td>
                <td>${fInscObj ? fInscObj.toLocaleDateString() : 'N/A'}</td>
                <td><span class="badge ${badgeClass}">${estadoTexto}</span></td>
                <td>${fFinObj ? fFinObj.toLocaleDateString() : '---'}</td>
                <td>${accionHtml}</td>
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
     
    loadCapacitacionesData(1);
});
