import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = [
    "form",
    "tipoUsuario",
    "departamento",
    "cargo",
    "campoEstado",
    "campoCargo",
    "campoDepartamento",
    "personaId",
    "modalLabel",
    "submitButton",
    "estado",
    "prefijoPais",
    "telefono",
    "fechaNacimiento",
    "accionInput",
  ];

  static values = {
    createUrl: String,
    editUrl: String,
  };

  connect() {
    this.toggleCampos();
  }

  setAccion(event) {
    const accion = event.currentTarget.dataset.personasAccion || "";
    this.accionInputTarget.value = accion;
  }

  startCreate() {
    this.formTarget.action = this.createUrlValue;
    this.modalLabelTarget.textContent = "Crear Nueva Persona";
    this.submitButtonTarget.textContent = "Guardar";
    this.personaIdTarget.value = "";
    this.accionInputTarget.value = "";
    this.clearErrors();
    this.clearFields();
    this.resetSelects();
    this.hideEstado();
    this.toggleCampos();
    this.showModal();
  }

  startEdit(event) {
    const button = event.currentTarget;
    const data = button.dataset;

    this.formTarget.action = this.editUrlValue;
    this.modalLabelTarget.textContent = "Editar Persona";
    this.submitButtonTarget.textContent = "Actualizar";
    this.personaIdTarget.value = data.id || "";
    this.accionInputTarget.value = "";

    this.clearErrors();
    this.clearFields();

    this.setValue("id_nombre", data.nombre);
    this.setValue("id_apellido", data.apellido);
    this.setValue("id_dni", data.dni);
    this.setValue("id_email", data.email);
    this.setValue("id_prefijo_pais", data.prefijo);
    this.setValue("id_telefono", data.telefono);
    this.setValue("id_fecha_nacimiento", data.fechaNacimiento);
    this.setValue("id_genero", data.genero);
    this.setValue("id_pais", data.pais);
    this.setValue("id_provincia", data.provincia);
    this.setValue("id_ciudad", data.ciudad);
    this.setValue("id_calle", data.calle);
    this.setValue("id_numero", data.numero);

    this.tipoUsuarioTarget.value = data.tipoUsuario || "";
    this.toggleCampos();

    if (data.estado) {
      this.estadoTarget.value = data.estado;
      this.showEstado();
    } else {
      this.hideEstado();
    }

    if (data.departamento) {
      this.departamentoTarget.value = data.departamento;
    }

    // Cargar cargos si corresponde
    if (this.shouldShowCargos()) {
      this.cargarCargos(this.departamentoTarget.value, data.cargo);
    } else {
      this.resetCargoSelect();
    }

    this.showModal();
  }

  onTipoUsuarioChange() {
    this.toggleCampos();
    const tipo = this.tipoUsuarioTarget.value;
    if (["2", "3", "4"].includes(tipo)) {
      this.cargarDepartamentos(tipo);
    } else {
      this.resetDepartamentoSelect();
      this.resetCargoSelect();
    }
  }

  onDepartamentoChange() {
    const deptId = this.departamentoTarget.value;
    if (this.shouldShowCargos()) {
      this.cargarCargos(deptId);
    } else {
      this.resetCargoSelect();
    }
  }

  confirmDelete(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const personaId = button.dataset.id;
    const personaNombre = button.dataset.nombre || "";

    Swal.fire({
      title: "¿Eliminar persona?",
      text: personaNombre
        ? `Esta acción eliminará a ${personaNombre}.`
        : "Esta acción no se puede deshacer.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#d33",
      cancelButtonColor: "#6c757d",
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        const form = document.getElementById("formEliminarPersona");
        form.action = `/personas/${personaId}/eliminar/`;
        form.submit();
      }
    });
  }

  toggleCampos() {
    const tipo = this.tipoUsuarioTarget.value;
    const tienePersona = Boolean(this.personaIdTarget.value);

    if (tipo === "5") {
      this.hideDepartamento();
      this.hideCargo();
      this.hideEstado();
      return;
    }

    const mostrarDepartamento = ["2", "3", "4"].includes(tipo);
    const mostrarCargo = tipo === "2";
    const mostrarEstado = mostrarDepartamento && tienePersona;

    this.setVisibility(this.campoDepartamentoTarget, mostrarDepartamento);
    this.setVisibility(this.campoCargoTarget, mostrarCargo);
    this.setVisibility(this.campoEstadoTarget, mostrarEstado);
  }

  shouldShowCargos() {
    return this.tipoUsuarioTarget.value === "2";
  }

  cargarDepartamentos(tipoUsuario) {
    this.departamentoTarget.innerHTML = '<option value="">Cargando...</option>';
    fetch(`/personas/departamentos_por_tipoUsuario/${tipoUsuario}`)
      .then((response) => response.json())
      .then((data) => {
        this.resetDepartamentoSelect();
        if (!data.departamentos || data.departamentos.length === 0) {
          this.departamentoTarget.innerHTML =
            '<option value="">No hay departamentos disponibles</option>';
          return;
        }

        this.departamentoTarget.innerHTML =
          '<option value="">Seleccione un departamento</option>';
        data.departamentos.forEach((departamento) => {
          const option = document.createElement("option");
          option.value = departamento.id;
          option.textContent = departamento.nombre;
          this.departamentoTarget.appendChild(option);
        });
      });
  }

  cargarCargos(deptId, selectedCargo = "") {
    if (!deptId) {
      this.resetCargoSelect();
      return;
    }

    this.cargoTarget.innerHTML = '<option value="">Cargando...</option>';
    fetch(`/personas/cargos_por_departamento/${deptId}`)
      .then((response) => response.json())
      .then((data) => {
        this.resetCargoSelect();
        if (!data.cargos || data.cargos.length === 0) {
          this.cargoTarget.innerHTML =
            '<option value="">No hay cargos disponibles</option>';
          return;
        }

        this.cargoTarget.innerHTML =
          '<option value="">Seleccione un cargo</option>';
        data.cargos.forEach((cargo) => {
          const option = document.createElement("option");
          option.value = cargo.id;
          option.textContent = cargo.nombre;
          if (cargo.vacante === 0) {
            option.disabled = true;
            option.style.color = "gray";
          }
          if (selectedCargo && String(cargo.id) === String(selectedCargo)) {
            option.selected = true;
          }
          this.cargoTarget.appendChild(option);
        });
      });
  }

  clearErrors() {
    this.element
      .querySelectorAll("#modalPersona .text-danger, #modalPersona .errorlist")
      .forEach((el) => el.remove());
    this.formTarget
      .querySelectorAll(".is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  clearFields() {
    const ids = [
      "id_nombre",
      "id_apellido",
      "id_dni",
      "id_email",
      "id_prefijo_pais",
      "id_telefono",
      "id_fecha_nacimiento",
      "id_pais",
      "id_provincia",
      "id_ciudad",
      "id_calle",
      "id_numero",
    ];

    ids.forEach((id) => this.setValue(id, ""));
    this.tipoUsuarioTarget.value = "";
    this.estadoTarget.value = "";
  }

  resetSelects() {
    this.resetDepartamentoSelect();
    this.resetCargoSelect();
  }

  resetDepartamentoSelect() {
    this.departamentoTarget.innerHTML =
      '<option value="">Seleccione un departamento</option>';
  }

  resetCargoSelect() {
    this.cargoTarget.innerHTML = '<option value="">Seleccione un cargo</option>';
  }

  setValue(id, value) {
    const el = document.getElementById(id);
    if (el) {
      el.value = value || "";
    }
  }

  setVisibility(element, show) {
    element.style.display = show ? "block" : "none";
  }

  showEstado() {
    this.setVisibility(this.campoEstadoTarget, true);
  }

  hideEstado() {
    this.setVisibility(this.campoEstadoTarget, false);
  }

  hideDepartamento() {
    this.setVisibility(this.campoDepartamentoTarget, false);
  }

  hideCargo() {
    this.setVisibility(this.campoCargoTarget, false);
  }

  showModal() {
    const modalElement = document.getElementById("modalPersona");
    if (!modalElement) return;
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
    modalInstance.show();
  }
}
