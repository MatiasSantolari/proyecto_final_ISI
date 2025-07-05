from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls_auth')),
    path('', include('core.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
]