# exchange_relay/urls.py
from django.contrib import admin
from django.urls import path, include
from .views import DiagnosticView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_client.urls')),
    path('diagnostic/', DiagnosticView.as_view(), name='diagnostic'),
]