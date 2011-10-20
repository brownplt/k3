from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound
import os
import logging
import uuid
from apply.models import *
from django.db import IntegrityError
import belaylibs.dj_belay as bcap
from lib.py.common import logWith404
from belaylibs.models import Grant

logger = logging.getLogger('default')

def applicant_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed['GET']

  return render_to_response('application.html', {})

def new_account_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed['GET']

  return render_to_response('new_account.html', {})

def admin_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed['GET']

  return render_to_response('admin.html', {})

# Django middleware class to set handlers on every request
class ApplyInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, \
      { 'scorecategory-delete' : ScoreCategoryDeleteHandler, \
        'scorecategory-change' : ScoreCategoryChangeHandler, \
        'scorecategory-add' : ScoreCategoryAddHandler,\
        'scorevalue-change' : ScoreValueChangeHandler,\
        'applicantposition-add' : ApplicantPositionAddHandler,\
        'area-add' : AreaAddHandler,\
        'area-delete' : AreaDeleteHandler,\
        'add-reviewer': AddReviewerRelationshipHandler,
        'add-admin': AddAdminRelationshipHandler,
        'request-new-reviewer': AddReviewerRequestHandler,
        'launch-reviewer': ReviewerLaunchHandler })
    return None

def checkPostArgs(classname, args, keys):
  for k in keys:
    if not args.has_key(k):
      return logWith404(classname + ' error: post args missing ' + k)
  return 'OK'

# Search for a department with name=dept_name and handle errors
# Returns (success, <department or response>)
def findDepartment(class_name, dept_name):
  depts = Department.objects.filter(name=dept_name)
  if len(depts) > 1:
    resp = logWith404(logger, class_name + ' fatal error: duplicate departments',\
      level='error')
    return (False, resp)
  if len(depts) == 0:
    resp = { \
      "success" : False, \
      "message" : "no department named %s" % deptname\
    }
    return (False, bcap.bcapResponse(resp))
  dept = depts[0]
  return (True, dept)

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

# Adds a new relationship with an admin
# One-shot capability
class AddAdminRelationshipHandler(bcap.CapHandler):
  # granted: UnverifiedUser
  def post(self, granted, args):
    unverified_user = granted.unverifieduser
    if granted is None:
      return HttpResponseNotFound()

    auth_info = AuthInfo(
      email=unverified_user.email, \
      name=unverified_user.name, \
      role='admin', \
      department=unverified_user.department)
    auth_info.save()

    # Remove the unverified_user---this is a one-shot request
    unverified_user.delete()
    # This is the capability to put in launch_info
    launch = bcap.grant('launch-reviewer', auth_info)
    return bcap.bcapResponse({
      'public_data': 'Admin account for %s' % auth_info.name,
      'private_data': launch,
      'domain': bcap.this_server_url_prefix(),
      'url': '/admin'
    })

# Adds a new relationship with a reviewer
# One-shot capability
class AddReviewerRelationshipHandler(bcap.CapHandler):
  # granted: UnverifiedUser
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
    unverified_user.delete()
    # This is the capability to put in launch_info
    launch = bcap.grant('launch-reviewer', reviewer)
    return bcap.bcapResponse({
      'public_data': 'Reviewer account for %s' % auth_info.name,
      'private_data': launch,
      'domain': bcap.this_server_url_prefix(),
      'url': '/review'
    })

class ReviewerLaunchHandler(bcap.CapHandler):
  def get(self, granted, args):
    return bcap.bcapNullResponse()

class ScoreCategoryDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = Grant.objects.filter(db_entity=grantable)
    if len(grants) == 0:
      return logWith404(logger, 'ScoreCategoryDeleteHandler fatal error: no grant')
    grantable.scorecategory.delete()
    return bcap.bcapNullResponse()

class ScoreCategoryChangeHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortform']

  def name_str(self):
    return 'ScoreCategoryChangeHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response
    sc = grantable.scorecategory
    sc.name = args['name']
    sc.shortform = args['shortform']
    sc.save()
    return bcap.bcapNullResponse() 

class ScoreCategoryAddHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortform']

  def name_str(self):
    return 'ScoreCategoryAddHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    name = args['name']
    shortform = args['shortform']
    
    sc = ScoreCategory(department=grantable.department, name=name, \
      shortform=shortform)
    try:
      sc.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'category already exists'}
      return bcap.bcapResponse(resp)

    delCap = bcap.grant('scorecategory-delete', sc)
    changeCap = bcap.grant('scorecategory-change', sc)

    resp = {"success" : True, "change" : changeCap, "delete" : delCap}
    return bcap.bcapResponse(resp)

class ScoreValueChangeHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['explanation']

  def name_str(self):
    return 'ScoreValueChangeHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response
    sv = grantable.scorevalue
    sv.explanation = args['explanation']
    sv.save()
    return bcap.bcapNullResponse()

class ApplicantPositionAddHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortform', 'autoemail']

  def name_str(self):
    return 'ApplicantPositionAddHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    name = args['name']
    shortform = args['shortform']
    autoemail = args['autoemail']

    position = ApplicantPosition(department=grantable.department, name=name,\
      shortform=shortform)
    try:
      position.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'position already exists'}
      return bcap.bcapResponse(resp)

    return bcap.bcapResponse({'success' : True})

class AreaAddHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'abbr']

  def name_str(self):
    return 'AreaAddHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    name = args['name']
    abbr = args['abbr']
    
    area = Area(department=grantable.department, name=name, abbr=abbr)
    try:
      area.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'area already exists'}
      return bcap.bcapResponse(resp)

    delCap = bcap.grant('area-delete', area)
    return bcap.bcapResponse({'success' : True, 'delete' : delCap})

class AreaDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = Grant.objects.filter(db_entity=grantable)
    if len(grants) == 0:
      return logWith404(logger, 'ARDeleteHandler fatal error: no grant')
    area = grantable.area
    area.delete()
    return bcap.bcapNullResponse()
