import logging
import uuid
import hashlib
import os
import subprocess

from django.core.validators import validate_email
from django.http import HttpResponseNotFound, HttpResponseNotAllowed

import settings

from contwinue.models import *
from contwinue.email import send_and_log_email, notFoundResponse
import contwinue.email_strings as strings
import contwinue.submitter as submitter

import belaylibs.dj_belay as bcap

from lib.py.common import logWith404, make_get_handler

logger = logging.getLogger('default')

index_handler = make_get_handler('login.html', {})

def conf_from_path(request):
  path = request.path_info
  slash = path.find('/', 1)
  if slash == -1: return (True, logWith404(logger, 'Badly formed path: %s' % path))

  shortname = path[1:slash]
  return (False, Conference.get_by_shortname(shortname))

def get_launch(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  key = args['key']
  account = get_one(Account.objects.filter(key=key))
  if key is None: return logWith404('Bad account: %s' % key)

  return bcap.bcapResponse(account.get_launchables())

def create_user(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf

  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  key = args['key']
  account = get_one(Account.objects.filter(key=key))
  if key is None: return logWith404('Bad account: %s' % key)

  gcreds = get_one(GoogleCredentials.objects.filter(account=account))

  if get_one(User.objects.filter(email=gcreds.email)):
    return bcap.bcapResponse({'error': True, 'message': 'Account exists'})
  user = User(username=gcreds.email,
              email=gcreds.email,
              full_name=u'',
              conference=conf,
              account=account)
  user.save()
  user.roles.add(get_one(Role.objects.filter(name='user')))

  paper = Paper(contact=user,
                author=args['email'],
                title=u'',
                target=conf.default_target,
                conference=conf)
  paper.save()

  paper.authors.add(user)
  paper.save()

  launchcap = bcap.grant('launch-paper', {'user': user, 'paper': paper})
  launchbase = '%s/paper' % bcap.this_server_url_prefix()

  launchable = Launchable(account=account,
                          launchbase=launchbase,
                          launchcap=bcap.cap_for_hash(launchcap),
                          display='See my papers')
  launchable.save()

  return bcap.bcapResponse(account.get_launchables())

def continue_login(request):
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  logger.error('ARGS: %s', args)

  email = args['email']
  password = args['password']

  creds = ContinueCredentials.objects.filter(username=email)

  for c in creds:
    salt = c.salt
    hashed_password = get_hashed(password, salt)
    if c.hashed_password == hashed_password:
      account = c.account
      return bcap.bcapResponse({'launch': c.account.get_launchables()})

  return bcap.bcapResponse({
    'error': True,
    'message': 'No account found for that email and password'
  })

def get_basic(request):
  (err, conference) = conf_from_path(request)
  if err: return logWith404(logger, 'Conf not found: %s' % shortname)

  return bcap.bcapResponse(conference.get_title_and_contact())

paper = make_get_handler('writer.html', {})



#######################################
# Admin Handlers
#######################################

class GetAdminHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_admin())

class GetAllHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_all())

class AddTopicHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name']

  def post(self, granted, args):
    conference = granted.conference
    name = args['name']

    if conference.has_topic_named(name):
      t = conference.get_topic_by_name(name)
    else:
      try:
        t = Topic(name=args['name'], conference=granted.conference)
        t.save()
      except Exception as e:
        return logWith404(logger, 'AddTopicHandler: %s' % e, level='error')

    return bcap.bcapResponse(t.to_json())

class DeleteTopicHandler(bcap.CapHandler):
  def delete(self, granted):
    topic = granted.topic
    try:
      topic.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteTopicHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddDecisionValueHandler(bcap.CapHandler):
  def post_arg_name(self):
    return ['abbr', 'description', 'targetable']

  def post(self, granted, args):
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']
    targetable = args['targetable']

    if conference.has_decision_value(targetable, abbr, description):
      ndv = conference.get_decision_value(targetable, abbr, description)
    else:
      try:
        ndv = DecisionValue(targetable=targetable, abbr=abbr, \
          description=description, conference=conference)
        ndv.save()
      except Exception as e:
        return logWith404(logger, 'AddDecisionValueHandler: %s' % e, level='error')

    return bcap.bcapResponse(ndv.to_json())

class DeleteDecisionValueHandler(bcap.CapHandler):
  def delete(self, granted):
    dv = granted.decisionvalue
    try:
      dv.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteDecisionHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddReviewComponentTypeHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['description', 'pcOnly']

  def post(self, granted, args): 
    conference = granted.conference
    description = args['description']
    pc_only = args['pcOnly']

    if conference.has_rc_type(description, pc_only):
      rct = conference.get_rc_type(description, pc_only)
    else:
      try:
        rct = ReviewComponentType(description=description, pc_only=pc_only,\
          conference=conference)
        rct.save()
      except Exception as e:
        return logWith404(logger, 'AddReviewComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(rct.to_json())

class AddComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args): 
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']

    if conference.has_component_type(abbr):
      ct = conference.component_type_by_abbr(abbr)
    else:
      try:
        ct = ComponentType(abbr=abbr, description=description,\
          fmt=args['format'], size_limit=args['sizelimit'],\
          deadline=args['deadline'], grace_hours=args['gracehours'],\
          mandatory=args['mandatory'], conference=conference)
        ct.save()
      except Exception as e:
        return logWith404(logger, 'AddComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(ct.to_json())

class DeleteComponentTypeHandler(bcap.CapHandler):
  def delete(self, granted):
    ct = granted.componenttype
    try:
      ct.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteComponentType: %' % e,\
        level='error')
    return bcap.bcapNullResponse()

class ChangeComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args):
    ct = granted.componenttype
    ct.fmt = args['format']
    ct.abbr = args['abbr']
    ct.description = args['description']
    ct.size_limit = args['sizelimit']
    ct.deadline = args['deadline']
    ct.grace_hours = args['gracehours']
    ct.mandatory = args['mandatory']

    try:
      ct.save()
    except Exception as e:
      return logWith404(logger, 'ChangeComponentType: %' % e,\
        level='error')
    
    return bcap.bcapResponse(ct.to_json())

class ChangeUserEmailHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def post(self, granted, args):
    user = granted.user
    try:
      user.email = args['email']
      user.save()
    except Exception as e:
      return logWith404(logger, 'ChangeUserEmailHandler: %s' % e,\
        level='error')

    return bcap.bcapResponse('true')

# In contwinue.py, this is handle_getIDsByDecision
# Here, instead of passing the decision value ID, the decision value is part
# of the grant
class GetPapersOfDVHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted['conference'].conference
    decision_value = granted['decision_value'].decisionvalue

    return bcap.bcapResponse(conference.papers_of_dv(decision_value))

class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'user-update-name': submitter.UserUpdateNameHandler,

      'add-password': submitter.AddPasswordHandler,
      'add-google-account': submitter.AddGoogleAccountHandler,
      'add-paper': submitter.AddPaperHandler,
      'writer-basic': submitter.WriterBasicHandler,
      'writer-paper-info': submitter.WriterPaperInfoHandler,
      'author-text': submitter.AuthorTextHandler,
      'paper-deadline-extensions': submitter.PaperDeadlineExtensionsHandler,
      'paper-set-title': submitter.PaperSetTitleHandler,
      'paper-add-author': submitter.AddAuthorHandler,
      'paper-remove-author': submitter.RemoveAuthorHandler,
      'paper-set-author': submitter.PaperSetAuthorHandler,
      'paper-set-pcpaper': submitter.PaperSetPcPaperHandler,
      'paper-set-target': submitter.PaperSetTargetsHandler,
      'paper-set-topics': submitter.PaperSetTopicsHandler,
      'paper-update-components': submitter.PaperUpdateComponentsHandler,
      'get-component-file': submitter.GetComponentFileHandler,
      'launch-paper': submitter.LaunchPaperHandler,
      'launch-new-paper': submitter.LaunchNewPaperHandler,
      'launch-attach-to-paper': submitter.LaunchAttachToPaperHandler,
      # End LaunchPaper handlers

      'get-papers-of-dv': GetPapersOfDVHandler,
      'get-admin': GetAdminHandler,
      'get-all': GetAllHandler,
      'add-topic': AddTopicHandler,
      'delete-topic': DeleteTopicHandler,
      'add-decision-value': AddDecisionValueHandler,
      'delete-decision-value': DeleteDecisionValueHandler,
      'add-review-component-type': AddReviewComponentTypeHandler, 
      'add-component-type': AddComponentTypeHandler,
      'delete-component-type': DeleteComponentTypeHandler,
      'change-component-type': ChangeComponentTypeHandler,
      'change-user-email': ChangeUserEmailHandler,
      # End LaunchAdmin handlers

      # End LaunchContinue handlers

      # End LaunchMeeting handlers

      # End LaunchPaperView handlers
    })
    return None
