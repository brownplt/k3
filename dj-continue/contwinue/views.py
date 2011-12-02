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
  if slash == -1: return (True, logWith404(logger, 'Badly formed path: %s' % path))

  shortname = path[1:slash]
  return (False, Conference.get_by_shortname(shortname))

def create_user(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf

  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  key = args['key']
  account = get_one(Account.objects.filter(key=key))
  
  user = User(username=account.email,
              email=account.email,
              fullname=args['name'],
              conference=conf)
  user.save()
  user.roles.add(get_one(Role.objects.filter(name='user')))
  user.save()

  paper = Paper(contact=user,
                author=args['name'],
                title=u'',
                target=conf.default_target,
                conference=conf)
  paper.save()

  launchcap = bcap.grant('launch-paper', paper)
  launchbase = '%s/paper' % bcap.this_server_url_prefix()

  launch = Launchable(account=account,
                      launchbase=launchbase,
                      launchcap=launchcap,
                      public='Paper (no title yet)')
  launch.save()

  return bcap.bcapResponse(account.get_launchables())

def get_basic(request):
  (err, conference) = conf_from_path(request)
  if err: return logWith404(logger, 'Conf not found: %s' % shortname)

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

class PaperSetTargetsHandler(bcap.CapHandler):
  def post_arg_names(self): return ['targetID', 'othercats']  
  def post(self, granted, args):
    paper = granted.paper
    paper.update_target_by_id(args['targetID'])
    paper.update_othercats(args['othercats'])
    paper.save()
    paper.conference.update_last_change(paper)
    return bcap.bcapResponse(paper.get_paper())

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

class PaperUpdateComponentsHandler(bcap.CapHandler):
  def post_arg_names(): []
  def post_with_files(self, granted, args, files):
    thetime = time.time()
    paper = granted.paper
    conf = paper.conference
    def check_deadlines_and_save(args, saver):
      for key, val in args.iteritems():
        ct = conf.component_type_by_abbr(key)
        if ct is None: continue
        deadline = ct.deadline
        de = DeadlineExtension.get_by_ct_and_paper(ct, paper)
        if not (de is None):
          deadline = de.until
        if (thetime > deadline+(ct.gracehours*3600)):
          # Differs from contwinue.py:  All the files are in the files dict
          excomp = get_one(Component.objects.filter(type=ct, paper=paper))
          if (not excomp) or (excomp.value != val):
            ret = {'error': 'You cannot upload a component after its deadline.'}
          continue
        excomp = get_one(Component.objects.filter(type=ct, paper=paper))
        saver(ct, excomp)

    def saveText(ct, excomp):
      if ct.fmt == 'Text':
        if excomp: excomp.delete() # TODO(joe): deleting the same as destroySelf()?
        newcomp = Component(
          conference=conf, type=ct, paper=paper,
          lastSumbitted=int(thetime), # use thetime again---all submitted simultaneously
          value=val, # TODO(joe): escaping?
          mimetype='text/plain'
        )
      else:
        raise Exception('Non-text component in args dictionary')

    def saveFile(ct, comp):
      pass

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
      'setTarget': bcap.regrant('paper-set-target', paper),
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
      'paper-set-target': PaperSetTargetsHandler,
      'paper-set-topics': PaperSetTopicsHandler,
      'launch-paper': LaunchPaperHandler
      # End LaunchPaper handlers

      
      # End LaunchAdmin handlers

      
      # End LaunchContinue handlers

      # End LaunchMeeting handlers

      # End LaunchPaperView handlers
    })
    return None

