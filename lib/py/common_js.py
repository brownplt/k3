from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound
import settings
import logging
logger = logging.getLogger('default')

def common_js_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])    
  return render(request, 'lib/js/common.js', {
    'belay_location': settings.BELAY_LOCATION
  }, content_type='text/javascript')
