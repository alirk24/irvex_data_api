# exchange_relay/urls.py
from django.contrib import admin
from django.urls import path, include
from .views import DiagnosticView,DebugApiView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_client.urls')),
    path('diagnostic/', DiagnosticView.as_view(), name='diagnostic'),
    path('debug/trigger-fetch/', DebugApiView.as_view(), name='debug-api'),
]
# api_client/urls.py
from django.urls import path
from .views import StockDataView

urlpatterns += [
    path('stocks/', StockDataView.as_view(), name='all-stocks'),
    path('stocks/<str:stock_code>/', StockDataView.as_view(), name='stock-detail'),
]