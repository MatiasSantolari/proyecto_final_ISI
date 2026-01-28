from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.auth.views import oauth_complete_safe

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls_auth')),
 #   path('personas/', include('personas.urls')),
    path('', include('core.urls')),
    path('oauth/complete/<str:backend>/', oauth_complete_safe, name='social_complete'),
    path('oauth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)