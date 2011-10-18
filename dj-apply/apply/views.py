from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound
import os
import logging
import uuid
from apply.models import *

import belaylibs.dj_belay as bcap
from lib.py.common import logWith404
from belaylibs.models import Grant

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
        'sc-add' : SCAddHandler,\
        'sv-change' : SVChangeHandler,\
        'add-reviewer': AddReviewerRelationshipHandler,
        'request-new-reviewer': AddReviewerRequestHandler })
    return None

# Gets a capability that is handed off to will-be reviewers.
# It will be included in the fragment on a page that asks them
# for information and creates their relationship.
# This is a relatively powerful capability --- it should only
# be accessible from Admin views.
class AddReviewerRequestHandler(bcap.CapHandler):
  # granted: Department
  # args: { 'name': str, 'email': str }
  def post(self, granted, args):
    department = granted.department
    unverified_reviewer = UnverifiedUser( \
      role='reviewer', \
      name=args['name'], \
      email=args['email'], \
      department=department)

    unverified_reviewer.save()
    create_account = bcap.grant('add-reviewer', unverified_reviewer)
    return bcap.bcapResponse(create_account)

# Adds a new relationship with a reviewer
# One-shot capability
class AddReviewerRelationshipHandler(bcap.CapHandler):
  # granted: UnverifiedUser
  # args: any
  # (args are ignored, but post makes sense because of side-effects)
  def post(self, granted, args):
    unverified_user = granted.unverifieduser
    if granted is None:
      return HttpResponseNotFound()

    auth_info = AuthInfo(
      email=unverified_user.email, \
      name=unverified_user.name, \
      role='reviewer', \
      department=unverified_user.department)
    auth_info.save()

    reviewer = Reviewer(
      auth=auth_info, \
      committee=False, \
      department=unverified_user.department)
    reviewer.save()

    # Remove the unverified_user---this is a one-shot request
    granted.delete()
    return bcap.bcapNullResponse()

class SCDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = Grant.objects.filter(db_entity=grantable)
    if len(grants) == 0:
      return logWith404(logger, 'SCDeleteHandler fatal error: no grant')
    sc = grantable.scorecategory
    values = ScoreValue.objects.filter(category=sc)
    for v in values:
      Score.objects.filter(value=v).delete()
      v.delete()
    sc.delete()
    grants.delete()
    return bcap.bcapNullResponse()

class SCChangeHandler(bcap.CapHandler):
  def post(self, grantable, args):
    if not args.has_key('name'):
      return logWith404(logger, 'SCChangeHandler: post args missing name')
    if not args.has_key('shortform'):
      return logWith404(logger, 'SCChangeHandler: post args missing shortform')
    sc = grantable.scorecategory
    sc.name = args['name']
    sc.shortform = args['shortform']
    sc.save()
    return bcap.bcapNullResponse() 

class SCAddHandler(bcap.CapHandler):
  def post(self, grantable, args):
    if not args.has_key('name'):
      return logWith404(logger, 'SCChangeHandler: post args missing name')
    if not args.has_key('shortform'):
      return logWith404(logger, 'SCChangeHandler: post args missing shortform')
    if not args.has_key('department'):
      return logWith404(logger, 'SCChangeHandler: post args missing department')

    name = args['name'] 
    short = args['shortform']
    deptname = args['department']
    depts = Department.objects.filter(name=deptname)
    if len(depts) > 1:
      return logWith404(logger, 'SCChangeHandler fatal error: duplicate departments',\
        level='error')
    if len(depts) == 0:
      resp = { \
        "success" : False, \
        "message" : "no department named %s" % deptname\
      }
      return bcap.bcapResponse(resp)
    dept = depts[0]

    categories = ScoreCategory.objects.filter(department=dept, name=name, \
      shortform=short)
    if len(categories) > 0:
      resp = {\
        "success" : False,\
        "message" : "category already exists"\
      }
      return bcap.bcapResponse(resp)

    sc = ScoreCategory(department=dept, name=name, shortform=short)
    sc.save()

    delCap = bcap.grant('sc-delete', sc)
    changeCap = bcap.grant('sc-change', sc)

    resp = {\
      "success" : True,\
      "change" : changeCap,\
      "delete" : delCap\
    }
    return bcap.bcapResponse(resp)

class SVChangeHandler(bcap.CapHandler):
  def post(self, grantable, args):
    if not args.has_key('explanation'):
      return logWith404(logger, 'SVChangeHandler: post args missing explanation')
    sv = grantable.scorevalue
    explanation = args['explanation']
    sv.explanation = explanation
    sv.save()
    return bcap.bcapNullResponse()
