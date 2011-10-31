from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpRequest
from station.models import StationData, LaunchInfo, Relationship
import os
import logging
import uuid
from urlparse import urlparse

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
    responses['newInstance'] = bcap.grant('new_instance', station)
    responses['instances'] = bcap.grant('instances', station)
    return bcap.bcapResponse(responses)

  def post(self, station, args):
    return HttpResponse('LaunchHandler POST NYI')

class NewInstanceHandler(bcap.CapHandler):
  def get(self, station):
    return HttpResponse('NewInstanceHandler GET NYI')

  def post(self, station, args):
    domain = args['domain']
    url = args['url']
    logger.error("Domain: %s, URL: %s" % (domain, url))
    private_data = bcap.dataPreProcess(str(args['private_data']))
    logger.error("PD: %s" % private_data)
    logger.error("PuD: %s" % args['public_data'])
    public_data = bcap.dataPreProcess(str(args['public_data']))
    logger.error("PuDpp: %s" % args['public_data'])

    try:
      launch_info = LaunchInfo(domain=domain, \
                               url=url, \
                               private_data=private_data, \
                               public_data=public_data)
      launch_info.save()
    except Exception as e:
      logger.error("Exception: %s" % e)
    logger.error("PD: %s, PUD: %s" % (private_data, public_data))

    instance_uuid = uuid.uuid4()
    instance_id = str(instance_uuid)

    logger.error("iid: %s" % instance_id)
    instance = Relationship(station=station, \
        instance_id =instance_id, \
        launch_info = launch_info)
    instance.save()

    return bcap.bcapResponse(bcap.grant('instance', instance))

class InstanceHandler(bcap.CapHandler):
  def get(self, granted):
    instance = granted.relationship
    launch_info = instance.launch_info
    response = {}
    response['domain'] = launch_info.domain
    response['url'] = launch_info.url
    response['private_data'] = bcap.dataPostProcess(launch_info.private_data)
    response['public_data'] = bcap.dataPostProcess(launch_info.public_data)
    return bcap.bcapResponse(response)
  def post(self, granted, args):
    return HttpResponse('InstanceHandler POST NYI') 

class InstancesHandler(bcap.CapHandler):
  def get(self, station):
    instances = Relationship.objects.filter(station=station)
    response = [bcap.grant('instance', i) for i in instances]
    return bcap.bcapResponse(response)
  def post(self, item):
    return HttpResponse('InstancesHandler POST NYI') 
