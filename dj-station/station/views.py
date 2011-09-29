from django.http import HttpResponse, HttpRequest
from station.models import StationData, InstanceData, SectionData
import os
import logging
import uuid

import belaylibs.dj_belay as bcap

logger = logging.getLogger('default')

def cap(url):
  return { '@': url }

def server_url(path):
  return bcap.this_server_url_prefix() + path

def keyName(key):
  if isinstance(key, str):
    return key
  if isinstance(key, unicode):
    return key
  return key.name()

def launch_url(stationKey):
  return server_url('/belay/launch?s=' + keyName(stationKey))

def instances_url(stationKey):
  return server_url('/instances?s=' + keyName(stationKey))

def instance_url(stationKey, instanceKey):
  return server_url('/instance?s=' + keyName(stationKey)
    + '&i=' + keyName(instanceKey))

def generate(request):
  if request.method == 'GET':
    station_uuid = uuid.uuid4()
    station_id = str(station_uuid)
    return bcap.bcapResponse(cap(launch_url(station_id)))

  # only GET is allowed
  return HttpResponseNotAllowed(['GET'])

def validate_station(request):
  station_uuid = uuid.UUID(request.GET['s'])
  station_id = str(station_uuid)
  try:
    station = StationData.objects.get(key=station_id)
  except StationData.DoesNotExist:
    station = StationData(key=station_id)
  return station

def launch(request):
  def do_launch(t):
    station = validate_station(request)
    station.save() 

    html = "/your-sites.html"
      
    reply = {
      'page': { 'html': server_url(html) },
      'info': {
        'instances': cap(instances_url(station.key)),
        'instanceBase': instance_url(station.key, '')
      }
    }

    return bcap.bcapResponse(reply)

  if request.method == 'GET':
    return do_launch('new')
  if request.method == 'POST':
    params = bcap.bcapRequest()
    return do_launch(params.get('version', 'new'))
  return HttpResponseNotAllowed(['GET', 'POST'])

def instances(request):
  return HttpResponse("Getting instances NYI")

def instance(request):
  return HttpResponse("Getting instance NYI")
