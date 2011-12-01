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

class AuthorTextHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.conference.get_author_text())

class PaperDeadlineExtensionsHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.paper.get_deadline_extensions())

class PaperSetTitleHandler(bcap.CapHandler):
  def post_arg_names(self): return ['title']
  def post(self, granted, args):
    granted.paper.title = args['title']
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetAuthorHandler(bcap.CapHandler):
  def post_arg_names(self): return ['author']
  def post(self, granted, args):
    granted.paper.author = args['author']
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetPcPaperHandler(bcap.CapHandler):
  def post_arg_names(self): return ['pcpaper']
  def post(self, granted, args):
    if args['pcpaper'] == 'yes':
      granted.paper.pc_paper = True
    else:
      granted.paper.pc_paper = False
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetTopicsHandler(bcap.CapHandler):
  def post_arg_names(self): return ['topics']
  def post(self, granted, args):
    paper = granted.paper
    paper.topic_set.clear()
    for t in args['topics']:
      for topic in Topic.get_by_conference_and_id(paper.conference, t):
        topic.papers.add(paper)
        topic.save()
    paper.save()
    paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class LaunchPaperHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted['paper'].paper

    return bcap.bcapResponse({
      'getPaper': bcap.regrant('writer-paper-info', granted),
      'getBasic': bcap.regrant('writer-basic', paper.conference),
      'getAuthorText': bcap.regrant('author-text', paper.conference),
      'setTitle': bcap.regrant('paper-set-title', paper),
      'setAuthor': bcap.regrant('paper-set-author', paper),
      'setPcPaper': bcap.regrant('paper-set-pcpaper', paper),
      'setTopics': bcap.regrant('paper-set-topics', paper),
      'getDeadlineExtensions': bcap.regrant('paper-deadline-extensions', paper)
    })

class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'writer-basic': WriterBasicHandler,
      'writer-paper-info': WriterPaperInfoHandler,
      'author-text': AuthorTextHandler,
      'paper-deadline-extensions': PaperDeadlineExtensionsHandler,
      'paper-set-title': PaperSetTitleHandler,
      'paper-set-author': PaperSetAuthorHandler,
      'paper-set-pcpaper': PaperSetPcPaperHandler,
      'paper-set-topics': PaperSetTopicsHandler,
      'launch-paper': LaunchPaperHandler
      # End LaunchPaper handlers

    })
    return None

