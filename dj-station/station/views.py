from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpRequest
from station.models import StationData, LaunchInfo, Relationship
import os
import logging
import uuid
from urlparse import urlparse

import belaylibs.dj_belay as bcap

logger = logging.getLogger('default')

def testpost(request):
  return render_to_response('test.html')

# Django middleware class to set handlers on every request
class StationInit():
  def process_request(self, request):
    logger.info(request.POST)
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
    responses['newInstance'] = bcap.grant('new_instance', station)
    responses['instance'] = bcap.grant('instance', station)
    responses['instances'] = bcap.grant('instances', station)
    return bcap.bcapResponse(responses)

  def post(self, station):
    return HttpResponse('LaunchHandler POST NYI')

class NewInstanceHandler(bcap.CapHandler):
  def get(self, station):
    return HttpResponse('NewInstanceHandler GET NYI')

  def post(self, station):
    logger.info(self.request.POST)
    domain = urlparse(bcap.this_server_url_prefix()).netloc
    url = self.request.path_info
    private_data = self.request.POST['private_data']
    launch_info = LaunchInfo(domain=domain, url=url, private_data=private_data)
    launch_info.save()

    instance_uuid = uuid.uuid4()
    instance_id = str(instance_uuid)

    r = Relationship(station=station, \
        instance_id =instance_id, \
        launch_info = launch_info)
    r.save()

    return bcap.bcapResponse({ "instance" : instance_id })

class InstanceHandler(bcap.CapHandler):
  def get(self, station):
    return HttpResponse('InstanceHandler GET NYI') 
  def post(self, station):
    try:
      instance_id = self.request.POST['instance_id']
    except KeyError:
      return bcap.bcapResponse({})

    instances = Relationship.objects.filter(\
        station=station, \
        instance_id=instance_id)
    
    if len(instances) > 1:
      raise bcap.BelayException("fatal: multiple instances with the same id")

    if len(instances) == 0:
      return bcap.bcapResponse({})

    instance = instances[0]
    launch_info = instance.launch_info
    response = {}
    response['domain'] = launch_info.domain
    response['url'] = launch_info.url
    response['private_data'] = launch_info.private_data
    return bcap.bcapResponse(response)

class InstancesHandler(bcap.CapHandler):
  def get(self, station):
    instances = Relationship.objects.filter(station=station)
    response = {}
    for instance in instances:
      launch_info = instance.launch_info
      current = {}
      current['domain'] = launch_info.domain
      current['url'] = launch_info.url
      current['private_data'] = launch_info.private_data
      response[str(instance.instance_id)] = current
    return bcap.bcapResponse(response)
  def post(self, item):
    return HttpResponse('InstancesHandler POST NYI') 
