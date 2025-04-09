from django import forms
from .models import Persona, Cargo, Departamento

class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)

##########################

ESTADO_EMPLEADO_CHOICES = [
    ('activo', 'Activo'),
    ('inactivo', 'Inactivo'),
    ('suspendido', 'Suspendido'),
]

class PersonaForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=ESTADO_EMPLEADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'})
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_cargo'})
    )

    class Meta:
        model = Persona
        fields = '__all__'  
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Apellido'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el DNI'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Email'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Teléfono'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la Dirección'}),
            'tipo_persona': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(PersonaForm, self).__init__(*args, **kwargs)
        self.fields['cargos'].required = False 
    

#############################


class CargoForm(forms.ModelForm):
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
