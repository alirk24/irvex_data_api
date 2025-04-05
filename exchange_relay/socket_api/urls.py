
# Add to socket_api/urls.py
from django.urls import path
from .views import AllStocksDebugView,WebSocketTestView,WebSocketDebugView

urlpatterns = [
    path('test/', WebSocketTestView.as_view(), name='websocket-test'),
    path('debug/', WebSocketDebugView.as_view(), name='websocket-debug'),
    path('all-stocks/', AllStocksDebugView.as_view(), name='all-stocks-debug'),
]