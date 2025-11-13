
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from core.constants import ROL_USUARIO_CHOICES

class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, persona=None, rol='normal'):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        
        usuario = self.model(
            username=username,
            email=self.normalize_email(email),
            persona=persona,
            rol=rol
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, email, password):
        usuario = self.create_user(username, email, password, rol='admin')
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario


class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    
    persona = models.OneToOneField(
        'Persona',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='id_persona'
    )

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)

    rol = models.CharField(max_length=10, choices=ROL_USUARIO_CHOICES, default='normal')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

 #   estado = models.CharField(
 #       max_length=10,
 #       choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
 #       default='activo'
 #   )

    # Estos tres campos determinan el acceso al admin de Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuario'

    def __str__(self):
        return f"{self.username} ({self.rol})"
