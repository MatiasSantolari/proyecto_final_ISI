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
        user.correo = self.cleaned_data["email"]
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
            'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        }),
        input_formats=['%Y-%m-%d'],
        required=True
    )

    prefijo_pais = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': '(Ej: +54)'
    }))

    telefono = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Número Teléfono'
    }))

    pais = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'País'
    }))
    provincia = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Provincia'
    }))
    ciudad = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Ciudad'
    }))
    calle = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Calle'
    }))
    numero = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Número'
    }))

    genero_choices=[
        ('', 'Elegir género'), 
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
    ]
    genero = forms.ChoiceField(
        choices=genero_choices,
        widget=forms.Select(attrs={
            'class': 'form-select bg-transparent text-white border-white ps-4 pe-5',
            'placeholder': 'Género'
        }),
        required=True
    )
    nombre = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Nombre',
        'required': True,
    }))
    apellido = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Apellido',
        'required': True,
    }))
    dni = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'DNI',
        'required': True,
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control bg-transparent text-white border-white ps-4 pe-5',
        'placeholder': 'Correo electrónico',
        'required': True,
    }))

    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono', 'prefijo_pais', 'fecha_nacimiento', 'pais', 
                  'provincia', 'ciudad', 'calle', 'numero', 'genero']


############

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
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),

            'prefijo_pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+54'}),
            'numero_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1123456789'}),

            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Género'}),

            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Provincia'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'calle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
        }

    def __init__(self, *args, **kwargs):
        super(PersonaForm, self).__init__(*args, **kwargs)
        self.fields['cargos'].required = False 
    

#############################


class CargoForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=CategoriaCargo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_categoria'})
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
        exclude = ['departamentos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Nombre del Cargo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese una Descripción','rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].required = False



#############################


class CategoriaCargoForm(forms.ModelForm):
    class Meta:
        model = CategoriaCargo
        fields = '__all__' 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el Nombre de la Categoria del Cargo'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese una Descripción de la categoria','rows': 3}),
        }