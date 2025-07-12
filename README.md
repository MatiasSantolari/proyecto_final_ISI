# proyecto_final_ISI
proyecto final de la carrera de ISI de UTN FRRo

Instalar:
pip install social-auth-app-django
pip install python-dotenv
pip install Pillow
pip install django-widget-tweaks


Pasos para configurar la Base de datos con Django
crear usuario en mysql con los datos:
         'NAME': 'apprrhh',
        'USER': 'facu',
        'PASSWORD': 'Facu1234',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    
Instalar el Conector de MySQL
Si aún no lo tienen instalado, deben ejecutar:
    pip install mysqlclient
    
Si hay errores, intentar con:
    pip install pymysql
    
Y agregar esto en __init__.py de la app principal:
    import pymysql
    pymysql.install_as_MySQLdb()

Generar las Migraciones
    python manage.py makemigrations
    python manage.py migrate

Crear un Superusuario (Opcional, para acceder al Admin de Django)
    python manage.py createsuperuser

Probar la Conexión
Ejecutar el servidor de Django:
    python manage.py runserver 8000

Y acceder utilizando:
http://127.0.0.1:8000