from django.http import HttpResponse, HttpRequest
from station.models import StationData, SectionData
import os
import logging
import uuid

import belaylibs.dj_belay as bcap

logger = logging.getLogger('default')

# Django middleware class to set handlers on every request
class StationInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, \
        {'launch' : LaunchHandler, \
          'new_instance' : NewInstanceHandler, \
          'instance' : InstanceHandler, \
          'instances' : InstancesHandler})
    return None

def generate(request):
  if request.method == 'GET':
    station_uuid = uuid.uuid4()
    station_id = str(station_uuid)
    station = StationData(sid=station_id)
    station.save()

    cap = bcap.grant('launch', station)
    return bcap.bcapResponse(cap)
  else:
    return HttpResponseNotAllowed(['GET'])

class LaunchHandler(bcap.CapHandler):
  def get(self, station):
    responses = {}
    responses['ni_cap'] = bcap.grant('new_instance', station)
    responses['i_cap'] = bcap.grant('instance', station)
    responses['is_cap'] = bcap.grant('instances', station)
    return bcap.bcapResponse(responses)

  def post(self, station, args):
    return HttpResponse('LaunchHandler POST NYI')

class NewInstanceHandler(bcap.CapHandler):
  def get(self, station):
    return HttpResponse('NewInstanceHandler GET NYI')

  def post(self, station, args):
    domain = urlparse.urlparse(bcap.this_server_url_prefix()).netloc
    url = request.path_info
    private_data = request.POST['private_data']
    launch_info = LaunchInfo(domain=domain, url=url, private_data=private_data)
    launch_info.save()

    instance_uuid = uuid.uuid4()
    instance_id = str(instance_uuid)

    r = Relationship(station=station, \
        instance_id =instance_id, \
        launch_info = launch_info)
    r.save()

    return HttpResponse('NewInstanceHandler finished')

class InstanceHandler(bcap.CapHandler):
  def get(self, item):
    return HttpResponse('InstanceHandler GET NYI') 
  def post(self, item, args):
    return HttpResponse('InstanceHandler POST NYI') 

class InstancesHandler(bcap.CapHandler):
  def get(self, item):
    return HttpResponse('InstancesHandler GET NYI') 
  def post(self, item, args):
    return HttpResponse('InstancesHandler POST NYI') 

"""
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
"""
