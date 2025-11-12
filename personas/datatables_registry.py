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
            "searching": True,
            "language": {"search": "Buscar: ","searchPlaceholder": "Ingrese DNI.."}
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
