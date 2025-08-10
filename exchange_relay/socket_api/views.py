from django.shortcuts import render
from django.views.generic import TemplateView

class WebSocketTestView(TemplateView):
    template_name = 'socket_api/test.html'

class WebSocketDebugView(TemplateView):
    template_name = 'socket_api/debug.html'
    

class AllStocksDebugView(TemplateView):
    template_name = 'socket_api/all_stocks_debug.html'
    

class StockIdsDebugView(TemplateView):
    template_name = 'socket_api/stock_ids_debug.html'