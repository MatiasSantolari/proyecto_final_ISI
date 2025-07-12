from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import DateInput


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
    
    
##########################

ESTADO_EMPLEADO_CHOICES = [
    ('activo', 'Activo'),
    ('inactivo', 'Inactivo'),
    ('suspendido', 'Suspendido'),
]



class PersonaFormCreate(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        input_formats=['%Y-%m-%d'],
        required=True
    )

    prefijo_pais = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '(Ej: +54)'
    }))

    telefono = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: 1123456789'
    }))

    pais = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'País'
    }))
    
    provincia = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Provincia'
    }))
    
    ciudad = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ciudad'
    }))
    
    calle = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Calle'
    }))
    
    numero = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Número'
    }))

    genero_choices = [
        ('', 'Elegir género'), 
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
    ]

    genero = forms.ChoiceField(
        choices=genero_choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        required=True
    )

    nombre = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre',
    }))
    
    apellido = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Apellido',
    }))
    
    dni = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'DNI',
    }))

    avatar = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={
        'class': 'form-control'
    }))

    cvitae = forms.FileField(
    required=False,
    widget=forms.FileInput(attrs={
        'class': 'form-control d-none', 
        'accept': '.pdf,.zip',
        'id': 'id_cvitae',
    }))

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'dni',
            'telefono', 'prefijo_pais', 'fecha_nacimiento',
            'pais', 'provincia', 'ciudad',
            'calle', 'numero', 'genero', 'avatar', 'cvitae'
        ]


############

class PersonaForm(forms.ModelForm):
    tipo_usuario = forms.ChoiceField(
        choices=[
            ('normal', 'Normal'),
            ('empleado', 'Empleado'),
            ('jefe', 'Jefe'),
            ('gerente', 'Gerente'),
            ('admin', 'Administrador'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_usuario'}),
        required=False
    )

    estado = forms.ChoiceField(
        choices=ESTADO_EMPLEADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'})

    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'})
    )

    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_cargo'})
    )

    genero = forms.ChoiceField(
        choices=[
            ('', 'Elegir género'),
            ('masculino', 'Masculino'),
            ('femenino', 'Femenino'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    fecha_nacimiento = forms.DateField(
        widget=DateInput(format='%Y-%m-%d', attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        input_formats=['%Y-%m-%d'],
        required=True
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'})
    )

    avatar = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    cvitae = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control d-none',
            'accept': '.pdf,.zip',
            'id': 'id_cvitae',
        })
    )

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'dni', 'telefono', 'prefijo_pais', 'fecha_nacimiento',
            'pais', 'provincia', 'ciudad', 'calle', 'numero', 'genero', 'avatar', 'cvitae'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'prefijo_pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(Ej: +54)'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1123456789'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Provincia'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'calle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer departamento_id si fue pasado desde la vista
        departamento_id = kwargs.pop('departamento_id', None)
        super().__init__(*args, **kwargs)

        # Si hay un departamento, filtrar cargos en base a él
        if departamento_id:
            self.fields['cargo'].queryset = Cargo.objects.filter(
                id__in=CargoDepartamento.objects.filter(departamento_id=departamento_id).values_list('cargo_id', flat=True)
            )
        else:
            # Si no hay departamento, deshabilitar el campo o dejarlo vacío
            self.fields['cargo'].queryset = Cargo.objects.none()
    

#############################


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
