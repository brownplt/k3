# Copyright 2011 Brown University. All Rights Reserved.
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

"""Abstractions for writing Belay servers for Django."""

import datetime
import logging
import os
import base64
import uuid
import urlparse
import json
import re
import httplib
import settings
from cryptcaps import Crypt

from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest
from lib.py.common import logWith404

from models import Grant, Grantable

logger = logging.getLogger('default')

#TODO(joe): make this programmatic rather than a constant setting
def this_server_url_prefix():
  return settings.SITE_NAME

def cap_url(cap):
  return '%s%s' % (handlerData.prefix, cap)

def is_crypt_cap(capURL):
  return capURL.find(handlerData.crypt_prefix) == 0

def crypt_cap_url(cap):
  return '%s%s' % (handlerData.crypt_prefix, cap)

def cap_id_from_url(capURL):
  return capURL[handlerData.prefix_strip_length:]

def crypt_info_from_url(capURL):
  return capURL[handlerData.crypt_prefix_strip_length:]

def cap_for_hash(cap):
  ser = cap.serialize()
  if ser.find(handlerData.prefix) == 0:
    return handlerData.cap_prefix + cap_id_from_url(ser)
  return '/cryptcap/' + crypt_info_from_url(ser)

class BelayException(Exception):
  pass

#
# Capabilities
#

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
    result = handle(capURL, meth, data, {})
    # TODO(jpolitz): other Content-Types
    if re.match('image/.*', result['Content-Type']):
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
    elif result.has_header('Content-Disposition'):
      return result
    else:
      if result.status_code >= 400:
        raise BelayException('invokeCapURL Failed: %s ' % result)
      return dataPostProcess(result.content)
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
      response = invokeCapURL(self.ser, method, data=data)
    else:
      response = invokeCapURL(self.ser, method)

    return response

  def get(self):
    return self.invoke('GET')
  def put(self, data):
    return self.invoke('PUT', data)
  def post(self, data=None):
    return self.invoke('POST', data)
  def delete(self):
    return self.invoke('DELETE')
     
  def serialize(self):
    return self.ser

def dataPreProcess(data):
  class Decapitator(json.JSONEncoder):
    def default(self, obj):
      if isinstance(obj, Capability):
        return {'@': obj.serialize()}
      elif hasattr(obj, 'to_json'):
        return obj.to_json()
      else:
        return obj

  try:
    return json.dumps({'value': data}, cls=Decapitator)
  except TypeError as exn:
    logging.debug(str(exn))
    logging.debug("Unserializable: " + str(data))

def dataPreProcessV(data):
  class Decapitator(json.JSONEncoder):
    def default(self, obj):
      if isinstance(obj, Capability):
        return {'@': obj.serialize()}
      elif hasattr(obj, 'to_json'):
        return obj.to_json()
      else:
        return obj

  try:
    return json.dumps(data, cls=Decapitator)
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

def dbPreProcess(data):
  class Declassifier(json.JSONEncoder):
    def default(self, obj):
      if isinstance(obj, Grantable):
        return {'#': obj.id}
      else:
        return obj

  try:
    return json.dumps(data, cls=Declassifier)
  except TypeError as exn:
    logging.debug(str(exn))
    logging.debug("Unserializable: " + str(data))

def dbPostProcess(serialized):
  def classify(obj):
    if '#' in obj:
      grantables = Grantable.objects.filter(id=obj['#'])
      if len(grantables) == 0: return None
      else: return grantables[0]
    else:
      return obj

  try:
    return json.loads(serialized, object_hook=classify)
  except ValueError as exn:
    logging.debug(str(exn))
    logging.debug("Unloadable: " + str(serialized))
  

# Base class for handlers that process capability invocations.
class CapHandler(object):
  methods = ['get', 'put', 'post', 'delete']

  # Subclasses override if they handle file uploads
  myFiles = {}
  def files_needed(self):
    return []

  def all_files(self):
    return False

  def allowedMethods(self):
    return [m.upper() for m in self.methods if self.__class__.__dict__.has_key(m)]

  def post_arg_names(self):
    return []
  def name_str(self):
    return 'CapHandler'
  def checkPostArgs(self, args):
    for k in self.post_arg_names():
      if not args.has_key(k):
        return logWith404(logger, self.__class__.__name__ + ' error: post args missing %s, got %s' % (k, args))
    return 'OK'

  def setCurrentGrant(self, grant):
    self.current_grant = grant
  def getCurrentGrant(self):
    return self.current_grant
  def getCurrentCap(self):
    return Capability(handlerData.prefix + self.current_grant.cap_id)
  def updateGrant(self, new_data):
    self.current_grant.db_data = dbPreProcess(new_data)
    self.current_grant.save()

  def setArgs(self, args): self.args = args
  def getArgs(self):       return self.args

  def notAllowedResponse(self):
    return HttpResponseNotAllowed(self.allowedMethods())
  def get(self, grantable):
    return self.notAllowedResponse()
  def put(self, grantable, args):
    return self.notAllowedResponse()
  def post(self, grantable, args):
    return self.notAllowedResponse()
  def post_files(self, grantable, args):
    return self.notAllowedResponse()
  def delete(self, grantable):
    return self.notAllowedResponse()

default_prefix = 'cap'

class HandlerData(object):
  def __init__(self):
    self.path_to_handler = {}
    self.prefix = ''
    self.prefix_strip_length = 0
    self.is_set = False

def xhr_response(response):
  response['Access-Control-Allow-Origin'] = settings.ORIGINS

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

def bcapStringResponse(content):
  response = HttpResponse()
  xhr_content(response, content, "text/plain;charset=UTF-8")
  return response
  

handlerData = HandlerData()

def set_handlers(cap_prefix, path_map):
  global handler_data
  if handlerData.is_set:
    return

  crypt_prefix = 'crypt' + cap_prefix
  if not cap_prefix.startswith('/'):
    cap_prefix = '/' + cap_prefix
    crypt_prefix = '/' + crypt_prefix
  if not cap_prefix.endswith('/'):
    cap_prefix += '/'
    crypt_prefix += '/'
  
  handlerData.prefix = this_server_url_prefix() + cap_prefix
  handlerData.crypt_prefix = this_server_url_prefix() + crypt_prefix
  handlerData.cap_prefix = cap_prefix
  handlerData.prefix_strip_length = len(handlerData.prefix)
  handlerData.crypt_prefix_strip_length = len(handlerData.crypt_prefix)
  handlerData.is_set = True

  for url in path_map:
    set_handler(url, path_map[url])

def set_crypt_secret(secret):
  handlerData.crypt = Crypt(secret)

def get_handler(path):
  return handlerData.path_to_handler[path]

def set_handler(path, handler):
  handlerData.path_to_handler[path] = handler

def handle_cap_id(cap_id, method, args, files):
  grants = Grant.objects.filter(cap_id=cap_id)

  if len(grants) == 0:
    response = HttpResponse()
    return logWith404(logger, "Cap not found: %s" % cap_id)
    content = dataPreProcess("proxyHandler: Cap not found: %s" % cap_id)
    xhr_content(response, content, "text/plain;charset=UTF-8")
    response.status_code = 404
    return response

  if len(grants) > 1:
    # TODO(arjun.guha@gmail.com): appropriate error in response
    raise BelayException('%s, %s' % (self.request.path_info, cap_id))

  grant = grants[0]   
  path = str(grant.internal_path)
  handler_class = get_handler(path)
  handler = handler_class()
  handler.setCurrentGrant(grant)

  item = dbPostProcess(grant.db_data)
  return cap_invoke(item, args, handler, method, path, files)

def handle_crypt_cap(cryptdata, method, args, files):
  data = dbPostProcess(handlerData.crypt.unprepare(cryptdata))
  path = str(data['p'])
  handler_class = get_handler(path)
  handler = handler_class()
  item = data['d']
  return cap_invoke(item, args, handler, method, path, files)

def cap_invoke(item, args, handler, method, path, files, log=True):
  files_needed = handler.files_needed()
  using_files = len(files_needed) > 0
  if using_files:
    files_granted = dict([(n, files[n]) for n in files_needed if files.has_key(n)])
  elif handler.all_files():
    using_files = True
    files_granted = files
  handler_log = ""
  handler_log += 'Handler: %s\n' % str(path)
  handler_log += '  Time: %s\n' % datetime.datetime.now() 
  handler_log += ('  Args: %s\n' % str(args))

  handler.setArgs(args)

  try:
    if method == 'GET':
      response = handler.get(item)
    elif method == 'PUT':
      response = handler.put(item, args)
    elif method == 'POST':
      maybe_error_response = handler.checkPostArgs(args)
      if maybe_error_response != 'OK':
        logger.error("Post args check failed")
        logger.error(handler_log)
        return maybe_error_response
      if using_files:
        logger.error('Using files')
        response = handler.post_files(item, args, files_granted)
      else:
        logger.error('Not using files')
        response = handler.post(item, args)
    elif method == 'DELETE':
      response = handler.delete(item)
    else:
      response = HttpResponse()
      content = dataPreProcess("proxyHandler: Bad method: %s\n" % request.method)
      xhr_content(response, content, "text/plain;charset=UTF-8")
      response.status_code = 404
    # Don't log file responses
#    if hasattr(response, 'Content-Disposition') and\
#        response['Content-Disposition'].find('attachment') != -1:
    handler_log += '  Response: %s\n' % str(response)
    logger.error(handler_log)
    return response
  finally:
    logger.error(handler_log)
#  except Exception as e:
#    logger.error('BELAY: Uncaught handler exception: %s' % e)
#    raise e

def proxyHandler(request):

  # Allow cross-origin requests on capablities based on settings.ORIGINS
  def options():
    response = HttpResponse()

    m = request.META['HTTP_ACCESS_CONTROL_REQUEST_METHOD']
    h = request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']

    response["Access-Control-Allow-Origin"] = settings.ORIGINS
    response["Access-Control-Max-Age"] = 2592000
    response["Access-Control-Allow-Methods"] = 'POST' 
    if h:
      response["Access-Control-Allow-Headers"] = h
    else:
      pass
    xhr_content(response, "", "text/plain;charset=UTF-8")
    return response

  req_files = request.FILES
  post_args = request.POST
  get_args = request.GET
  args = dataPostProcess(request.read())

  def update_with(args, new_args):
    if len(new_args) > 0:
      if args is None:
        args = new_args
      else:
        args.update(new_args)
    return args

  args = update_with(args, get_args)
  args = update_with(args, post_args)

  logger.error('Args: %s' % args)

  if request.method == 'OPTIONS':
    return options()
  else:
    fullpath = this_server_url_prefix() + request.path_info
    logger.error('Path ' + fullpath)
    return handle(fullpath, request.method, args, req_files)

def handle(fullpath, method, args, files):
  maybe_cap = fullpath
  if is_crypt_cap(maybe_cap):
    return handle_crypt_cap(
      fullpath[len(handlerData.crypt_prefix):],
      method,
      args,
      files
    )
  else:
    return handle_cap_id(
      fullpath[handlerData.prefix_strip_length:],
      method,
      args,
      files
    )

# The default can be swapped around.  The longer names won't change.
def grant(path, data):
  return cryptgrant(path, data)
  
def cryptgrant(path, data):
  salt = os.urandom(8)
  data = {'p': path, 'd': data, 's': base64.b64encode(salt)}
  encrypted = handlerData.crypt.prepare(dbPreProcess(data))
  cap = crypt_cap_url(encrypted)
  logger.error('Cap: %s' % cap)
  return Capability(crypt_cap_url(encrypted))

def dbgrant(path, data):
  cap_id = str(uuid.uuid4())
  serialized = dbPreProcess(data)
  item = Grant(cap_id=cap_id, internal_path=path, db_data=serialized)
  item.save()
  return Capability(cap_url(cap_id))

def regrant(path, data):
  serialized = dbPreProcess(data)
  items = Grant.objects.filter(internal_path=path, db_data=serialized)
  if len(items) >= 1:
    return Capability(cap_url(items[0].cap_id))
  else:
    return grant(path, data)

def revoke(path_or_handler, entity):
  entity.grant_set.filter(internal_path=path).delete()

def revokeEntity(entity):
  entity.grant_set.delete()

