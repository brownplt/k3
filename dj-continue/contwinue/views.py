import logging

from django.http import HttpResponseNotFound, HttpResponseNotAllowed

import settings

from contwinue.models import *

import belaylibs.dj_belay as bcap
from belaylibs.models import Grant

from lib.py.common import logWith404, make_get_handler

logger = logging.getLogger('default')

index_handler = make_get_handler('login.html', {})

def conf_from_path(request):
  path = request.path_info
  slash = path.find('/', 1)
  if slash == -1: return logWith404(logger, 'Badly formed path: %s' % path)

  shortname = path[1:slash]
  return Conference.get_by_shortname(shortname)

def get_basic(request):
  conference = conf_from_path(request)
  if conference == None:
    return logWith404(logger, 'Conf not found: %s' % shortname)

  return bcap.bcapResponse(conference.get_title_and_contact())

class WriterBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic = granted.conference.get_writer_basic()
    return bcap.bcapResponse(basic)

class WriterPaperInfoHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted['paper'].paper
    return bcap.bcapResponse(paper.get_paper())

class PaperDeadlineExtensionsHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.paper.get_deadline_extensions())

class LaunchPaperHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted['paper'].paper

    return bcap.bcapResponse({
      'getPaper': bcap.regrant('writer-paper-info', granted),
      'getBasic': bcap.regrant('writer-basic', paper.conference),
      'getDeadlineExtensions': bcap.regrant('paper-deadline-extensions', paper)
    })

class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'writer-basic': WriterBasicHandler,
      'writer-paper-info': WriterPaperInfoHandler,
      'paper-deadline-extensions': PaperDeadlineExtensionsHandler,
      'launch-paper': LaunchPaperHandler

    })
    return None

