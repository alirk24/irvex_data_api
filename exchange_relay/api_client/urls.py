from django.contrib import admin
from django.urls import path, include
from .views import DiagnosticView, DebugApiView, StockDataView, StockMetadataView, AllStocksSummaryView, StockIdsView, StockNamesOnlyView, StockNameToIdView

urlpatterns = [
    path('stocks/', StockDataView.as_view(), name='all-stocks'),
    path('stocks/<str:stock_code>/', StockDataView.as_view(), name='stock-detail'),
    path('metadata/', StockMetadataView.as_view(), name='all-metadata'),
    path('metadata/<str:stock_id>/', StockMetadataView.as_view(), name='stock-metadata'),
    path('diagnostic/', DiagnosticView.as_view(), name='diagnostic'),
    path('debug/trigger-fetch/', DebugApiView.as_view(), name='debug-api'),
    path('stocks/summary/', AllStocksSummaryView.as_view(), name='all-stocks-summary'),
    path('stock-ids/', StockIdsView.as_view(), name='stock-ids'),  # Full stock data
    path('stock-names/', StockNamesOnlyView.as_view(), name='stock-names-only'),  # Only IDs and names
    path('name-to-id/', StockNameToIdView.as_view(), name='stock-name-to-id'),  # Reverse: names as keys, IDs as values
]
