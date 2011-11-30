import logging

from django.http import HttpResponseNotFound, HttpResponseNotAllowed

import settings

from contwinue.models import *

import belaylibs.dj_belay as bcap
from belaylibs.models import Grant

from lib.py.common import logWith404, make_get_handler

logger = logging.getLogger('default')

index_handler = make_get_handler('login.html', {})

def get_basic(request):
  path = request.path_info
  slash = path.find('/', 1)
  if slash == -1: return logWith404(logger, 'Badly formed path: %s' % path)

  logger.error('Slash: %s, Path: %s' % (slash, path))

  shortname = path[1:slash]
  conference = Conference.get_by_shortname(shortname)
  if conference == None:
    return logWith404(logger, 'Conf not found: %s' % shortname)

  return bcap.bcapResponse(conference.get_title_and_contact())

class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      
    })
    return None
