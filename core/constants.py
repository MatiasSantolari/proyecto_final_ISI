ESTADO_EMPLEADO_CHOICES = [
        (1, 'Activo'),
        (2, 'Inactivo'),
        (3, 'En licencia'),
        (4, 'Suspendido'),
        (5, 'En Periodo de Prueba'),
        (6, 'Jubilado'),
    ]
ESTADO_EMPLEADO_CHOICES2 = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('en licencia', 'En licencia'),
        ('suspendido', 'Suspendido'),
        ('en periodo de prueba', 'En Periodo de Prueba'),
        ('jubilado', 'Jubilado'),
    ]

ROL_USUARIO_CHOICES = [
        (1, 'Normal'),
        (2, 'Empleado'),
        (3, 'Jefe'),
        (4, 'Gerente'),
        (5, 'Administrador'),
    ]
ROL_USUARIO_CHOICES2=[
        ('normal', 'Normal'),
        ('empleado', 'Empleado'),
        ('jefe', 'Jefe'),
        ('gerente', 'Gerente'),
        ('admin', 'Administrador'),
        ]

ESTADOS = [
    (0, 'Eliminado'), 
    (1, 'Activado')
]