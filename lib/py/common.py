from django.http import HttpResponseNotFound
from django.shortcuts import render_to_response
import logging
import hashlib
import cjson

def toJSON(obj):
	return cjson.encode(obj)

def logWith404(logger, msg, level='info'):
  if level == 'debug':
    logger.debug(msg)
  if level == 'info':
    logger.info(msg)
  elif level == 'warn':
    logger.warn(msg)
  elif level == 'error':
    logger.error(msg)
  elif level == 'critical':
    logger.critical(msg)
  else:
    logger.warn('logWith404: invalid log level %s' % level)
    logger.warn('message was: ' % msg)
  return HttpResponseNotFound()

def make_get_handler(template, params):
  def handler(request):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['GET'])

    return render_to_response(template, params)
  return handler

HASH_ITERATIONS = 20
# TODO: non-ASCII characters can break this
# need to sanitize raw password
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.sha1()
    m1.update(salted)
    salted = m1.hexdigest()
  return salted

