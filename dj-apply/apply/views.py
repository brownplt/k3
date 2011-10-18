from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound
import os
import logging
import uuid
from apply.models import ScoreCategory, ScoreValue, Score, Department

import belaylibs.dj_belay as bcap
from belaylibs.models import Grant

logger = logging.getLogger('default')

def logWith404(msg, level='info'):
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

logger = logging.getLogger('default')

def applicant_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed['GET']

  return render_to_response('applicant.html', {})

# Django middleware class to set handlers on every request
class ApplyInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, \
      { 'sc-delete' : SCDeleteHandler, \
        'sc-change' : SCChangeHandler, \
        'sc-add' : SCAddHandler,
        'add-reviewer': AddReviewerRelationshipHandler,
        'request-new-reviewer': AddReviewerRequestHandler })
    return None

# Gets a capability that is handed off to will-be reviewers.
# It will be included in the fragment on a page that asks them
# for information and creates their relationship.
# This is a relatively powerful capability --- it should only
# be accessible from Admin views.
class AddReviewerRequestHandler(bcap.CapHandler):
  # granted: DepartmentInfo
  # args: { 'name': str, 'email': str, 'committee': {'true', 'false'}}
  def post(granted, args):
    unverified_reviewer = UnverifiedUser( \
      role='reviewer', \
      name=args['name'], \
      email=args['email'], \
      committee=args['committee'] == 'true', \
      department=granted)

    unverified_user.save()
    create_account = bcap.grant('add-reviewer', unverified_reviewer)
    return bcapResponse(create_account)

# Adds a new relationship with a reviewer
# One-shot capability
class AddReviewerRelationshipHandler(bcap.CapHandler):
  # granted: UnverifiedUser
  # args: any
  # (args are ignored, but post makes sense because of side-effects)
  def post(granted, args):
    if granted is None:
      return HttpResponseNotFound()

    auth_info = AuthInfo(
      email=granted.email, \
      name=granted.name, \
      role='reviewer', \
      department=granted.department)
    auth_info.save()

    reviewer = Reviewer(
      auth=auth_info, \
      committee=granted.committee, \
      department=granted.department)
    reviewer.save()

    # Remove the unverified_user---this is a one-shot request
    granted.delete()
    return bcapNullResponse()

# Create a ScoreCategory and return caps for its handlers
def scorecategory_test(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  if not (args.has_key('name')):
    return logWith404('scorecategory_test: post args missing name')
  if not (args.has_key('shortform')):
    return logWith404('scorecategory_test: post args missing shortform')
  if not (args.has_key('department')):
    return logWith404('scorecategory_test: post args missing department')

  depts = Department.objects.filter(name=args['department'])
  if len(depts) > 1:
    return logWith404('scorecategory_test: fatal error: multiple departments \
        with name = %s' % args['department'], level='error')
  if len(depts) == 0:
    department = Department(name=args['department'], shortname=args['department'],\
      lastChange=0, headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='', contactName='', contactEmail='name@example.com',\
      techEmail='name@example.com')
    department.save()
  else:
    department = depts[0]

  sc = ScoreCategory(name=args['name'], \
      shortform=args['shortform'], \
      department=department)
  sc.save()

  cap_names = ['sc-delete', 'sc-change', 'sc-add']
  caps = dict([(nm[3:], bcap.grant(nm, sc)) for nm in cap_names])
  return bcap.bcapResponse(caps)

class SCDeleteHandler(bcap.CapHandler):
  def get(self, grantable):
    return HttpResponseNotAllowed(['DELETE'])

  def put(self, grantable, args):
    return HttpResponseNotAllowed(['DELETE'])

  def post(self, grantable, args):
    return HttpResponseNotAllowed(['DELETE'])

  def delete(self, grantable):
    Grant.objects.filter(db_entity=grantable).delete()
    return bcap.bcapNullResponse()

class SCChangeHandler(bcap.CapHandler):
  def get(self, grantable):
    return HttpResponseNotAllowed(['POST'])

  def put(self, grantable, args):
    return HttpResponseNotAllowed(['POST'])

  def post(self, grantable, args):
    return bcap.bcapNullResponse() 

  def delete(self, grantable):
    return HttpResponseNotAllowed(['POST'])

class SCAddHandler(bcap.CapHandler):
  def get(self, grantable):
    return HttpResponseNotAllowed(['POST'])

  def put(self, grantable, args):
    return HttpResponseNotAllowed(['POST'])

  def post(self, grantable, args):
    return bcap.bcapNullResponse() 

  def delete(self, grantable):
    return HttpResponseNotAllowed(['POST'])
