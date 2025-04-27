
# Add to socket_api/urls.py
from django.urls import path


from .views import AllStocksDebugView, WebSocketTestView, WebSocketDebugView, StockIdsDebugView

urlpatterns = [
    path('test/', WebSocketTestView.as_view(), name='websocket-test'),
    path('debug/', WebSocketDebugView.as_view(), name='websocket-debug'),
    path('all-stocks/', AllStocksDebugView.as_view(), name='all-stocks-debug'),
    path('stock-ids/', StockIdsDebugView.as_view(), name='stock-ids-debug'),
]