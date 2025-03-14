from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from .empleado import Empleado

class UsuarioManager(BaseUserManager):
    def create_user(self, nombre_usuario, correo, contraseña, empleado, rol='empleado'):
        if not correo:
            raise ValueError("El usuario debe tener un correo electrónico")
        
        usuario = self.model(
            nombre_usuario=nombre_usuario,
            correo=self.normalize_email(correo),
            empleado=empleado,
            rol=rol
        )
        usuario.set_password(contraseña)  # Encripta la contraseña
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, nombre_usuario, correo, contraseña):
        usuario = self.create_user(nombre_usuario, correo, contraseña, None, rol='admin')
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario


class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, db_column="id_empleado")
    nombre_usuario = models.CharField(max_length=50, unique=True)
    correo = models.EmailField(max_length=100, unique=True)
    contraseña = models.CharField(max_length=255)   
    rol = models.CharField(
        max_length=10,
        choices=[('admin', 'Admin'), ('empleado', 'Empleado'), ('gerente', 'Gerente')],
        default='empleado'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=10,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )

    is_active = models.BooleanField(default=True)  
    is_staff = models.BooleanField(default=False)  # Controla acceso al admin

    objects = UsuarioManager()  

    USERNAME_FIELD = 'nombre_usuario'
    REQUIRED_FIELDS = ['correo']

    class Meta:
        db_table = 'usuario'  

    def __str__(self):
        return self.nombre_usuario
