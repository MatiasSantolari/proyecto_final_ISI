# proyecto_final_ISI
proyecto final de la carrera de ISI de UTN FRRo

Instalar:
pip install social-auth-app-django
pip install python-dotenv
pip install python-decouple
pip install Pillow
pip install django-widget-tweaks
pip install holidays

(para python 3.8)-->  pip install chatterbot==1.0.5
(para python 3.10 o 3.11)--> pip install chatterbot==1.0.8
(para python 3.12)--> pip install git+https://github.com/gunthercox/ChatterBot.git
pip install chatterbot-corpus
pip install spacy
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm


Pasos para configurar la Base de datos con Django
crear usuario en mysql con los datos:
         'NAME': 'apprrhh',
        'USER': ,
        'PASSWORD': ,
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
