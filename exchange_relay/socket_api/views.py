from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView

class WebSocketTestView(TemplateView):
    template_name = 'socket_api/test.html'
