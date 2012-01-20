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
import contwinue.admin as admin
import contwinue.reviewer as reviewer
import contwinue.paperview as paperview

import belaylibs.dj_belay as bcap

from lib.py.common import logWith404, make_get_handler, get_hashed

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
  user.roles.add(get_one(Role.objects.filter(name='writer')))

  paper = Paper.newPaper(
    contact=user,
    title=u'',
    conference=conf
  )

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
admin_handler = make_get_handler('admin.html', {})
review_handler = make_get_handler('review.html', {})
paperview_handler = make_get_handler('paperview.html', {})

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

      'configure-conference': admin.ConfigureHandler,
      'get-admin': admin.GetAdminHandler,
      'get-papers-of-dv': admin.GetPapersOfDVHandler,
      'get-all': admin.GetAllHandler,
      'add-topic': admin.AddTopicHandler,
      'delete-topic': admin.DeleteTopicHandler,
      'add-decision-value': admin.AddDecisionValueHandler,
      'delete-decision-value': admin.DeleteDecisionValueHandler,
      'add-review-component-type': admin.AddReviewComponentTypeHandler, 
      'add-component-type': admin.AddComponentTypeHandler,
      'delete-component-type': admin.DeleteComponentTypeHandler,
      'change-component-type': admin.ChangeComponentTypeHandler,
      'change-user-email': admin.ChangeUserEmailHandler,
      'set-role': admin.SetRoleHandler,
      'set-contact': admin.SetContactHandler,
      'send-emails': admin.SendEmailsHandler,
      'get-subreviewers': admin.GetSubReviewersHandler,
      'add-pcs': admin.AddPCsHandler,
      'launch-admin': admin.LaunchAdminHandler,
      # End LaunchAdmin handlers

      'get-abstracts': reviewer.GetAbstractsHandler,
      'get-abstract': reviewer.GetAbstractHandler,
      'get-user-bids': reviewer.GetUserBidsHandler,
      'update-bids': reviewer.UpdateBidsHandler,
      'update-decision': reviewer.UpdateDecisionHandler,
      'get-paper-summaries': reviewer.GetPaperSummariesHandler,
      'get-review-percentages': reviewer.GetReviewPercentagesHandler,
      'launch-reviewer' : reviewer.LaunchReviewerHandler,
      # End LaunchContinue handlers

      'get-paper': paperview.GetPaperHandler,
      'get-review': paperview.GetReviewHandler,
      'save-review': paperview.SaveReviewHandler,
      'get-by-role': paperview.GetByRoleHandler,
      'revert-review': paperview.RevertReviewHandler,
      'set-hidden': paperview.SetHiddenHandler,
      'set-deadline': paperview.SetDeadlineHandler,
      'get-deadlines': paperview.GetDeadlinesHandler,
      'assign-reviewers': paperview.AssignReviewersHandler,
      'get-comments': paperview.GetCommentsHandler,
      'post-comment': paperview.PostCommentHandler,
      'launch-paperview': paperview.LaunchPaperViewHandler
      # End LaunchPaperView handlers
    })
    bcap.set_crypt_secret(settings.PRIVATE_KEY)
    return None
