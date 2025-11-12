(function () {
  const registry = {};

  function parseOptions(optionString) {
    if (!optionString) return {};
    try {
      return JSON.parse(optionString);
    } catch (error) {
      console.warn("No se pudo parsear data-datatable-options:", error);
      return {};
    }
  }

  function initTables() {
    document.querySelectorAll('table[data-datatable="true"]').forEach((table) => {
      const tableId = table.getAttribute('id');
      const baseOptions = parseOptions(table.dataset.datatableOptions);
      const pageLength = parseInt(table.dataset.pageLength || '10', 10) || 10;
      const responsive = table.dataset.datatableResponsive !== 'false';

      const options = Object.assign(
        {
          responsive,
          pageLength,
          language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json',
          },
        },
        baseOptions
      );

      const instance = $(table).DataTable(options);
      if (tableId) {
        registry[tableId] = instance;
      }
    });
  }

  function bindFilters() {
    document.querySelectorAll('[data-datatable-filter]').forEach((element) => {
      const eventType =
        element.dataset.filterEvent ||
        (element.tagName === 'SELECT' ? 'change' : 'input');

      element.addEventListener(eventType, function () {
        const tableId = element.dataset.datatableFilter;
        const columnIndex = parseInt(element.dataset.column, 10);
        if (!tableId || Number.isNaN(columnIndex)) return;

        const table = registry[tableId];
        if (!table) return;

        let value = element.value || '';
        const emptyValue = element.dataset.emptyValue;
        if (emptyValue !== undefined && value === emptyValue) {
          value = '';
        }

        table.column(columnIndex).search(value).draw();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTables();
    bindFilters();
  });

  window.getDataTableInstance = function (tableId) {
    return registry[tableId];
  };
})();
