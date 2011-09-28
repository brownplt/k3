# Copyright 2011 Google Inc. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Abstractions for writing Belay servers for AppEngine."""

import logging
import os
import uuid
import urlparse
import json
import re
import httplib
import settings

logger = logging.getLogger(__name__)

#TODO(joe): make this programmatic rather than a constant setting
def this_server_url_prefix():
  return settings.SITE_NAME
 
class BelayException(Exception):
  pass
  


#
# Capabilities
#
def invokeLocalCap(capURL, method, data=""):
  """Invoke a locally defined cap using ProxyHandler"""
  handler = ProxyHandler()
  req = webapp.Request.blank(capURL)
  req.body = data
  handler.initialize(req, webapp.Response())

  if method == 'GET':
    handler.get()
  elif method == 'PUT':
    handler.put()
  elif method == 'POST':
    handler.post()
  elif method == 'DELETE':
    handler.delete()
  else:
    raise BelayException("invokeLocalCap: Bad method: " + method)

  return handler.response
  
# NOTE(jpolitz): BcapHandlers and urlfetch.fetch() return different data
# structures.  invokeCapURL() needs to handle both, since it simulates a
# local HTTP cap invocation through ProxyHandler.
# If the invocation is of a normal capability, the value of the invocation
# is processed normally.  However, if the response is an image, the form of
# the response is that of a urlfetch.fetch() response object in both cases:
# http://code.google.com/appengine/docs/python/urlfetch/responseobjects.html
def invokeCapURL(capURL, meth, data=""):
  parsed = urlparse.urlparse(capURL)
  prefix = this_server_url_prefix()

  parsed_prefix = parsed.scheme + "://" + parsed.netloc

  if parsed_prefix == prefix:
    result = invokeLocalCap(parsed.path, meth, data)
    # TODO(jpolitz): other Content-Types
    if re.match('image/.*', result.headers['Content-Type']):
      # TODO(jpolitz): is this sufficient wrapping?
      class Wrapper(object):
        def read(self):
          return result.out.getvalue()
        def getheader(self, name, default=None):
          if result.has_key(name):
            return result[name]
          return default
        def __init__(self):
          self.status = result.status_code

      return Wrapper()
    else:
      return dataPostProcess(result.out.getvalue())
  else:
    # TODO: https
    conn = httplib.HTTPConnection(parsed.netloc)
    conn.request(method=meth, url=parsed.path, body=data)
    result = conn.getresponse()

    if result.status >= 400 and result.status <= 600:
      raise BelayException('CapServer: remote invoke of ' + capURL + ' failed.')
    elif re.match('image/.*', result.getheader('Content-Type', '')):
      return result 
    else:
      return dataPostProcess(result.read())

class Capability(object):
  def __init__(self, ser):
    self.ser = ser

  def invoke(self, method, data = None):
    #TODO(jpolitz): separate impls in python---all are essentially implURLSync
    if data != None:
      response = invokeCapURL(self.ser, method, data=dataPreProcess(data))
    else:
      response = invokeCapURL(self.ser, method)

    return response
     
  def serialize(self):
    return self.ser

def dataPreProcess(data):
  class Decapitator(json.JSONEncoder):
    def default(self, obj):
      if isinstance(obj, Capability):
        return {'@': obj.serialize()}
      else:
        return obj

  try:
    return json.dumps({'value': data}, cls=Decapitator)
  except TypeError as exn:
    logging.debug(str(exn))
    logging.debug("Unserializable: " + str(data))

def dataPostProcess(serialized):
  def capitate(obj):
    if '@' in obj:
      return Capability(obj['@'])
    else:
      return obj
  try:
    return json.loads(serialized, object_hook=capitate)['value']
  except ValueError as exn:
    logging.debug(str(exn))
    logging.debug("Unloadable: " + str(serialized))

class BcapHandler(object):
  pass

def xhr_response(response):
  response['Access-Control-Allow-Origin'] = '*'

def xhr_content(response, content, content_type):
  xhr_response(response)
  response.write(content)
  response["Cache-Control"] = "no-cache"
  response["Content-Type"] = content_type
  response["Expires"] = "Fri, 01 Jan 1990 00:00:00 GMT"

def bcapNullResponse():
  response = HttpResponse()
  xhr_response(response)
  return response

def bcapResponse(content):
  response = HttpResponse()
  content = dataPreProcess(content)
  xhr_content(response, content, "text/plain;charset=UTF-8")
  return response


path_to_handler = {}
default_prefix = '/caps/'
prefix_strip_length = len(default_prefix)

def set_handlers(cap_prefix, path_map):
  if not cap_prefix.startswith('/'):
    cap_prefix = '/' + cap_prefix
  if not cap_prefix.endswith('/'):
    cap_prefix += '/'
  
  prefix_strip_length = len(cap_prefix)
  default_prefix = this_server_url_prefix() + cap_prefix
  for (url, handler) in path_map:
    set_handler(url, handler)

def get_handler(path):
  return path_to_handler[path]
def set_handler(path, handler):
  path_to_handler[path] = handler


def proxyHandler(request):
  cap_id = request.path_info[prefix_strip_length:]
  grants = Grant.objects.filter(cap_id=cap_id)

  if len(grants) == 0:
    response = xhr_content("proxyHandler: " + \
                           "Cap not found: %s\n" % cap_id)
    response.status_code = 404
    return response

  if len(grants) > 1:
    # TODO(arjun.guha@gmail.com): appropriate error in response
    raise BelayException('%s, %s' % (self.request.path_info, cap_id))
  
  grant = grants[0]   
  handler_class = path_to_handler[grant.internal_path]
  handler = handler_class()

  method = request.method
  item = grant.db_entity
  args = dataPostProcess(request.read())

  if method == 'GET':
    return handler.get(item)
  elif method == 'POST':
    return handler.post(args, item)
  elif method == 'DELETE':
    return handler.delete(item)
  elif method == 'PUT':
    return handler.put(args, item)
  else:
    response = xhr_content("proxyHandler: " + \
                           "Bad method: %s\n" % request.method)
    response.status_code = 404
    return response

def get_path(path_or_handler):
  if isinstance(path_or_handler, str):
    return path_or_handler
  elif issubclass(path_or_handler, CapHandler):
    return path_or_handler.default_internal_url
  else:
    raise BelayException('CapServer:get_path::expected string or CapHandler')
     

def grant(path_or_handler, entity):
  path = get_path(path_or_handler)
  cap_id = str(uuid.uuid4())
  item = Grant(cap_id=cap_id, internal_path=path, db_entity=entity)
  item.put()
  return Capability(ProxyHandler.default_prefix + cap_id)

def regrant(path_or_handler, entity):
  path = get_path(path_or_handler)
  items = Grant.all().filter("internal_path = ", path) \
                     .filter("db_entity = ", entity) \
                     .fetch(2)
  if(len(items) > 1):
    raise BelayException('CapServer:regrant::ambiguous internal_path in regrant')
  
  if len(items) == 1:
    return Capability(ProxyHandler.default_prefix + items[0].cap_id)
  else:
    return grant(path_or_handler, entity)

def revoke(path_or_handler, entity):
  path = get_path(path_or_handler)
  entity.grant_set.filter(internal_path=path).delete()

def revokeEntity(entity):
  entity.grant_set.delete()
