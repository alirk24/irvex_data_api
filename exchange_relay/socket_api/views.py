from django.shortcuts import render
from django.views.generic import TemplateView

class WebSocketTestView(TemplateView):
    template_name = 'socket_api/test.html'

class WebSocketDebugView(TemplateView):
    template_name = 'socket_api/debug.html'