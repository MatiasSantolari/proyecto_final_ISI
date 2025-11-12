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
            "dom": "Bfrtip",
            "buttons": ["excel", "pdf", "colvis"],
        },
        "filters": [
            {
                "element_id": "buscadorDNI",
                "table_id": "tablaPersonas",
                "column": 2,
                "event": "input",
                "placeholder": "Ingrese DNI..."
            },
            {
                "element_id": "filtroTipoUsuario",
                "table_id": "tablaPersonas",
                "column": 5,
                "event": "change",
                "empty_value": "todos",
            },
        ],
    },
)
