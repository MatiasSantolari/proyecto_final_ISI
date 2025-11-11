from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import DateInput
import holidays
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta



class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
            'placeholder': 'Correo electrónico',
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
            'placeholder': 'Nombre de usuario',
        })
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
            'placeholder': 'Contraseña',
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
            'placeholder': 'Confirmar contraseña',
        })
    )
    class Meta:
        model = Usuario  
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.rol = "normal"
        if commit:
            user.save()
        return user
    
    
class CargoForm(forms.ModelForm):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=True,
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'})
    )
    
    vacante = forms.IntegerField(
        label='Vacantes',
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cantidad de vacantes',
            'id': 'id_vacante'
        })
    )

    sueldo_base = forms.DecimalField(
        label='Sueldo base',
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el sueldo base del cargo',
            'step': '0.01',
            'id': 'id_sueldo_base'
        })
    )

    class Meta:
        model = Cargo
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Nombre del Cargo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese una Descripción','rows': 3}),
        }

##    def __init__(self, *args, **kwargs):
##        super().__init__(*args, **kwargs)
##        self.fields['categoria'].required = False

#############################



class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre', 'placeholder': 'Ingrese el Nombre'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_descripcion', 'placeholder': 'Ingrese una descripcion', 'rows': 3}),
        }


################################

class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = ['titulo', 'descripcion', 'fecha_fin', 'es_recurrente']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el Título'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la Descripción',
                'rows': 3
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_fecha_fin',
                'placeholder': 'Ingrese la Fecha de Fin'
            }),
            'es_recurrente': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

###################################
class BeneficioForm(forms.ModelForm):
    class Meta:
        model = Beneficio
        fields = ['descripcion', 'monto', 'porcentaje', 'fijo']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_descripcion',
                'placeholder': 'Ingrese la descripción'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_monto',
                'placeholder': 'Ingrese el monto',
                'step': '1'
            }),
            'porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese porcentaje (0 a 100)',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'fijo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get("monto")
        porcentaje = cleaned_data.get("porcentaje")

        if monto and porcentaje:
            raise forms.ValidationError('No puede ingresar ambos: monto y porcentaje.')
        if not monto and not porcentaje:
            raise forms.ValidationError('Debe ingresar monto o porcentaje.')
        return cleaned_data
    

###################################


class DescuentoForm(forms.ModelForm):
    class Meta:
        model = Descuento
        fields = ['descripcion', 'monto', 'porcentaje', 'fijo']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_descripcion',
                'placeholder': 'Ingrese la descripción'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_monto',
                'placeholder': 'Ingrese el monto',
                'step': '1'
            }),
            'porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese porcentaje (0 a 100)',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'fijo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get("monto")
        porcentaje = cleaned_data.get("porcentaje")

        if monto and porcentaje:
            raise forms.ValidationError('No puede ingresar ambos: monto y porcentaje.')
        if not monto and not porcentaje:
            raise forms.ValidationError('Debe ingresar monto o porcentaje.')
        return cleaned_data

##########################

class HabilidadForm(forms.ModelForm):
    class Meta:
        model = Habilidad
        fields = ['nombre', 'descripcion']


########################

class NominaForm(forms.ModelForm):
    class Meta:
        model = Nomina
        fields = [
            'empleado',
            'fecha_generacion',
            'monto_bruto',
            'total_descuentos',
            'monto_neto',
            'estado',
        ]
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_generacion': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'monto_bruto': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'total_descuentos': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'monto_neto': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

########################
class LogroForm(forms.ModelForm):
    class Meta:
        model = Logro
        fields = ['descripcion', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }


########################
# Feriados Argentina
ar_holidays = holidays.country_holidays('AR')

def contar_dias_habiles(fecha_inicio, fecha_fin):
    dias = 0
    actual = fecha_inicio
    while actual <= fecha_fin:
        if actual.weekday() < 5 and actual not in ar_holidays:  # Lunes-Viernes y no feriado
            dias += 1
        actual += timedelta(days=1)
    return dias


class VacacionesSolicitudForm(forms.ModelForm):
    class Meta:
        model = VacacionesSolicitud
        fields = ["fecha_inicio", "fecha_fin"]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get("fecha_inicio")
        fin = cleaned_data.get("fecha_fin")

        if not inicio or not fin:
            raise forms.ValidationError("Debes seleccionar ambas fechas.")

        if fin < inicio:
            raise forms.ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        dias = contar_dias_habiles(inicio, fin)
        cleaned_data["cant_dias_solicitados"] = dias
        return cleaned_data



###########################


class TipoContratoForm(forms.ModelForm):
    class Meta:
        model = TipoContrato
        fields = ["descripcion", "duracion_meses"]
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": "form-control", "id": "id_descripcion", "placeholder": "Descripción"}),
            "duracion_meses": forms.NumberInput(attrs={"class": "form-control", "id": "id_duracion_meses", "placeholder": "Duración en meses"}),
        }



class ContratoForm(forms.ModelForm):
    monto_extra_pactado = forms.DecimalField(
        label='Monto Extra Pactado',
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el Monto Extra (si fue pactado)',
            'step': '0.01',
            'id': 'id_monto_extra_pactado'
        })
    )

    class Meta:
        model = HistorialContrato
        fields = ['empleado', 'contrato', 'fecha_inicio', 'fecha_fin', 'condiciones', 'monto_extra_pactado', 'estado']
        widgets = {
            'empleado': forms.Select(attrs={"class": "form-select", "id": "id_empleado"}),
            'fecha_inicio': forms.DateInput(attrs={"type": "date", "class": "form-control", "id": "id_fecha_inicio"}),
            'fecha_fin': forms.DateInput(attrs={"type": "date", "class": "form-control", "id": "id_fecha_fin"}),
            'condiciones': forms.Textarea(attrs={"class": "form-control", 'placeholder': 'Ingrese las Condiciones del Contrato', "rows": 3, "id": "id_condiciones"}),
            'estado': forms.HiddenInput(attrs={"id": "id_estado"})
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empleado'].queryset = Empleado.objects.all().order_by('apellido')
        self.fields['empleado'].label_from_instance = (
            lambda obj: f"{obj.apellido} {obj.nombre} - "
                        f"{obj.empleadocargo_set.last().cargo if obj.empleadocargo_set.exists() else 'Sin cargo'}"
        )
        self.fields['contrato'].required = False
        self.fields['fecha_fin'].required = False
        self.fields['estado'].initial = "activo"
        self.fields['monto_extra_pactado'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("contrato")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if tipo and fecha_inicio and not fecha_fin:
            cleaned_data["fecha_fin"] = fecha_inicio + timedelta(days=tipo.duracion_meses * 30)

        return cleaned_data


###########################
class InstitucionForm(forms.ModelForm):
    telefono = forms.RegexField(
        regex=r'^\+?\d{7,15}$',
        error_messages={
            'invalid': "Ingrese un número de teléfono válido (ej: +5491123456789 o 1123456789)"
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Teléfono',
            'type': 'tel'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico',
        })
    )

    class Meta:
        model = Institucion
        fields = ['nombre', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la institución'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección'
            }),
        }


######################
class TipoCriterioForm(forms.ModelForm):
    class Meta:
        model = TipoCriterio
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripcion del Tipo de Criterio'
            }),
        }


####################
class CriterioForm(forms.ModelForm):
    class Meta:
        model = Criterio
        fields = ['tipo_criterio', 'descripcion']
        widgets = {
            'tipo_criterio': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el criterio'}),
        }


###################
class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ['descripcion', 'fecha_evaluacion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'id': 'id_descripcion', 'class': 'form-control'}),
            'fecha_evaluacion': forms.DateInput(attrs={'id': 'id_fecha_evaluacion', 'class': 'form-control', 'type':'date'}),
        }


class CalificacionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        criterios = kwargs.pop('criterios')
        super().__init__(*args, **kwargs)
        for c in criterios:
            self.fields[f'criterio_{c.id}'] = forms.FloatField(
                label=c.descripcion,
                min_value=0,
                max_value=10,
                widget=forms.NumberInput(attrs={'class':'form-control', 'step':'0.1'})
            )
