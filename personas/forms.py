from django import forms
from django.forms.widgets import DateInput
from core.constants import ROL_USUARIO_CHOICES, ESTADO_EMPLEADO_CHOICES

from core.models import (
    Cargo,
    CargoDepartamento,
    Departamento,
    Persona,
)

from personas.models import (
    Certificacion,
    DatoAcademico,
    ExperienciaLaboral,
)



ADMIN_FIELDS = ("tipo_usuario", "estado", "departamento", "cargo")


class PersonaForm(forms.ModelForm):
    tipo_usuario = forms.ChoiceField(
        choices=ROL_USUARIO_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_tipo_usuario"}),
        required=False,
    )

    estado = forms.ChoiceField(
        choices=ESTADO_EMPLEADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_estado"}),
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_departamento"}),
    )

    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_cargo"}),
    )

    genero = forms.ChoiceField(
        choices=[("", "Elegir género"), ("masculino", "Masculino"), ("femenino", "Femenino")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    fecha_nacimiento = forms.DateField(
        widget=DateInput(
            format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}
        ),
        input_formats=["%Y-%m-%d"],
        required=True,
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Correo electrónico"}
        ),
    )

    avatar = forms.ImageField(
        required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    cvitae = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "form-control d-none",
                "accept": ".pdf,.zip",
                "id": "id_cvitae",
            }
        ),
    )

    class Meta:
        model = Persona
        fields = [
            "nombre",
            "apellido",
            "dni",
            "telefono",
            "prefijo_pais",
            "fecha_nacimiento",
            "pais",
            "provincia",
            "ciudad",
            "calle",
            "numero",
            "genero",
            "avatar",
            "cvitae",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre"}
            ),
            "apellido": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apellido"}
            ),
            "dni": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "DNI"}
            ),
            "prefijo_pais": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+54",
                    "style": "max-width: 90px;",
                }
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "123-456789"}
            ),
            "pais": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "País"}
            ),
            "provincia": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Provincia"}
            ),
            "ciudad": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ciudad"}
            ),
            "calle": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Calle"}
            ),
            "numero": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Número"}
            ),
        }

    def __init__(self, *args, **kwargs):
        departamento_id = kwargs.pop("departamento_id", None)
        include_admin_fields = kwargs.pop("include_admin_fields", True)

        super().__init__(*args, **kwargs)

        if not include_admin_fields:
            for field in ADMIN_FIELDS:
                self.fields.pop(field, None)
            return

        tipo_usuario = None
        if self.data:
            tipo_usuario = self.data.get("tipo_usuario")
        elif self.initial:
            tipo_usuario = self.initial.get("tipo_usuario")
        if not tipo_usuario and getattr(self.instance, "id", None):
            usuario = getattr(self.instance, "usuario", None)
            if usuario:
                tipo_usuario = getattr(usuario, "rol", None)

        if "departamento" in self.fields:
            departamentos_qs = Departamento.objects.all()
            if tipo_usuario != "admin":
                departamentos_qs = departamentos_qs.exclude(nombre__iexact="ADMIN")
            self.fields["departamento"].queryset = departamentos_qs

        if "cargo" not in self.fields:
            return

        if tipo_usuario == "admin":
            self.fields["cargo"].queryset = Cargo.objects.none()
            return

        cargos_qs = Cargo.objects.all()

        if tipo_usuario == "jefe":
            cargos_qs = cargos_qs.filter(es_jefe=True)
        if tipo_usuario == "empleado":
            cargos_qs = cargos_qs.filter(es_jefe=False, es_gerente=False)

        if tipo_usuario != "admin":
            cargos_qs = cargos_qs.exclude(
                id__in=CargoDepartamento.objects.filter(
                    departamento__nombre__iexact="ADMIN"
                ).values_list("cargo_id", flat=True)
            )

        if departamento_id:
            cargos_qs = cargos_qs.filter(
                id__in=CargoDepartamento.objects.filter(
                    departamento_id=departamento_id, vacante__gt=0
                ).values_list("cargo_id", flat=True)
            )

        self.fields["cargo"].queryset = cargos_qs


class DatoAcademicoForm(forms.ModelForm):
    class Meta:
        model = DatoAcademico
        fields = ["carrera", "institucion", "situacion_academica", "fecha_inicio", "fecha_fin"]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }


class CertificacionForm(forms.ModelForm):
    class Meta:
        model = Certificacion
        fields = ["nombre", "institucion", "fecha_inicio", "fecha_fin"]


class ExperienciaLaboralForm(forms.ModelForm):
    class Meta:
        model = ExperienciaLaboral
        fields = [
            "cargo_exp",
            "empresa",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "actualidad",
        ]
