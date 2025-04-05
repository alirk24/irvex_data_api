from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/exchange/$', consumers.ExchangeDataConsumer.as_asgi()),
    re_path(r'ws/exchange/all-stocks/$', consumers.AllStocksDataConsumer.as_asgi()),
]