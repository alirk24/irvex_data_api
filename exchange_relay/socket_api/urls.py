
# Add to socket_api/urls.py
from django.urls import path
from .views import WebSocketTestView

urlpatterns = [
    path('test/', WebSocketTestView.as_view(), name='websocket-test'),
]