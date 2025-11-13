from core.utils.datatables import register_datatable

register_datatable(
    "personas",
    {
        "table_id": "tablaPersonas",
        "options": {
            "responsive": True,
            "pageLength": 10,
            "order": [[0, "asc"]],
            "columnDefs": [
                {"orderable": False, "targets": -1},
            ],
            "dom": 
                    "<'row mb-2'<'col-sm-4'B><'col-sm-4 text-center'l><'col-sm-4'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
     "              <'row mt-2'<'col-sm-5'i><'col-sm-7'p>>",
            "buttons": ["excel", "pdf", "colvis"],
            "searching": True,
            "language": {"search": "Buscar: ","searchPlaceholder": "Ingrese DNI..", "emptyTable": "No se encontraron personas"}
        },
        "filters": [
            {
                "element_id": "filtroTipoUsuario",
                "table_id": "tablaPersonas",
                "column": 2,
                "event": "change",
                "empty_value": "todos",
            },
        ],
    },
)
