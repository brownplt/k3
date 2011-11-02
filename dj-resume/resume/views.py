from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound
import os
import logging
import uuid
from resume.models import *
from django.db import IntegrityError
import belaylibs.dj_belay as bcap
from lib.py.common import logWith404
from belaylibs.models import Grant

logger = logging.getLogger('default')

# TODO: implement
def sendLogEmail(msg, address):
  logger.error('send log email:\n %s \n%s' % (address, msg))

def applicant_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('application.html', {})

def new_account_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('new_account.html', {})

def admin_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('admin.html', {})

def review_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('review.html', {})

def index_handler(request):
  if request.method != 'GET':
    return HttpResponseNotAllowed(['GET'])

  deptkey = request.path_info.split('/')[1]
  logger.warn("Path_info: %s" % request.path_info)
  
  try:
    dept = Department.departmentByName(deptkey)
    cap = bcap.grant('add-applicant', dept)
    return render_to_response('index.html', {
      'create_applicant': bcap.grant('add-applicant', dept).serialize()
    })
  except Exception as e:
    return logWith404(logger, "Looked up bad department: %s, %s" % (deptkey, e), level='error')

# Django middleware class to set handlers on every request
class ResumeInit():
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
        'add-applicant': AddApplicantRelationshipHandler,
        'add-admin': AddAdminRelationshipHandler,
        'launch-reviewer': ReviewerLaunchHandler,
        'launch-admin': AdminLaunchHandler,
        'launch-applicant' : ApplicantLaunchHandler,\
        'unverifieduser-addrev' : UnverifiedUserAddRevHandler, 
        'unverifieduser-delete' : UnverifiedUserDeleteHandler,
        'unverifieduser-getpending' : UnverifiedUserGetPendingHandler,
        'get-reviewers' : GetReviewersHandler,
        'change-contacts' : ChangeContactsHandler,\
        'find-refs' : FindRefsHandler,\
        'get-basic' : GetBasicHandler,\
        'set-basic' : SetBasicHandler,\
        'get-reviewer' : GetReviewerHandler,\
        'get-applicants' : GetApplicantsHandler,\
        'add-applicant-with-position' : UnverifiedApplicantAddHandler,\
        'add-verified-applicant' : AddVerifiedApplicantHandler,\
        'request-reference' : RequestReferenceHandler,\
        'submit-contact-info' : SubmitContactInfoHandler,\
        'get-applicant' : GetApplicantHandler,\
        'get-csv' : GetCSVHandler })
    return None

def checkPostArgs(classname, args, keys):
  for k in keys:
    if not args.has_key(k):
      return logWith404(classname + ' error: post args missing ' + k)
  return 'OK'

class AddApplicantRelationshipHandler(bcap.CapHandler):
  def get(self, granted):
    dept = granted.department
    positions = dept.getPositions()
    caps = {}
    for p in positions:
      caps[p.name] = bcap.grant('add-applicant-with-position', p)
    return bcap.bcapResponse(caps)

class AdminLaunchHandler(bcap.CapHandler):
  def get(self, granted):
    department = granted.authinfo.department
    resp = {\
      'getReviewers' : bcap.grant('get-reviewers', department),\
      'UnverifiedUserAddRev' : bcap.grant('unverifieduser-addrev', department),\
      'UnverifiedUserGetPending' : bcap.grant('unverifieduser-getpending', department),\
      'ScoreCategoryAdd' : bcap.grant('scorecategory-add', department),\
      'ApplicantPositionAdd' : bcap.grant('applicantposition-add', department),\
      'AreaAdd' : bcap.grant('area-add', department),\
      'getBasic' : bcap.grant('get-basic', department),\
      'setBasic' : bcap.grant('set-basic', department),\
      'findRefs' : bcap.grant('find-refs', department),\
      'changeContacts' : bcap.grant('change-contacts', department),\
      'getCSV' : bcap.grant('get-csv', department)\
    }
    return bcap.bcapResponse(resp)

class ApplicantLaunchHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    department = applicant.department
    resp = {\
      'getBasic' : bcap.grant('get-basic', department),\
      'requestReference' : bcap.grant('request-reference', applicant),\
      'submitContactInfo' : bcap.grant('submit-contact-info', applicant),\
      'get' : bcap.grant('get-applicant', applicant)\
    }
    return bcap.bcapResponse(resp)

class RequestReferenceHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'institution', 'email']

  def name_str(self):
    return 'RequestReferenceHandler'

  def post(self, granted, args):
    return logWith404('request-reference NYI')

class SubmitContactInfoHandler(bcap.CapHandler):
  def post(self, granted, args):
    applicant = granted.applicant
    for (key, val) in args.iteritems():
      if key.find('comp-') == 0:
        id = key[5:]
        applicant.componentUpdate(id, val)
    return bcap.bcapResponse({'success' : True})

class GetApplicantHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    return bcap.bcapResponse(applicant.to_json())

class AddVerifiedApplicantHandler(bcap.CapHandler):
  def post(self, granted, args):
    ua = granted.unverifiedapplicant
    if granted is None:
      return HttpResponseNotFound()

    auth_info = AuthInfo(
      email=ua.email, \
      # TODO(matt): fix or remove name from AuthInfo?
      name='applicant name goes here',\
      role='applicant', \
      department=ua.department)
    auth_info.save()

    applicant = Applicant(\
      auth = auth_info,\
      firstname='applicant firstname',\
      lastname='applicant lastname',\
      country='applicant country',\
      department=ua.department,\
      position=ua.position\
    )
    applicant.save()

    ua.delete()
    launch = bcap.grant('launch-applicant', applicant)
    return bcap.bcapResponse({
      'public_data': 'Application for %s' % ua.email,
      'private_data': launch,
      'domain': bcap.this_server_url_prefix(),
      'url': '/static/application.html'
    })

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
    launch = bcap.grant('launch-admin', auth_info)
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

    reviewer = Reviewer(auth=auth_info, department=unverified_user.department)
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
  def get(self, granted):
    department = granted.reviewer.auth.department
    return bcap.bcapResponse({
      'getBasic': bcap.regrant('get-basic', department),
      'getReviewer': bcap.regrant('get-reviewer', granted),
      'getApplicants': bcap.regrant('get-applicants', granted)
    })

class GetReviewerHandler(bcap.CapHandler):
  def get(self, granted):
    reviewer = granted.reviewer
    ret = {
      'hiddens': reviewer.hiddenIds(),
      'highlights': reviewer.highlightIds(),
      'drafts': reviewer.draftIds(),
      'auth': {'role' : 'reviewer'}
    }
    return bcap.bcapResponse(ret)

class GetApplicantsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['lastChange']

  def post(self, grantable, args):
    reviewer = grantable.reviewer
    applicant_json = [a.to_json() for a in reviewer.getApplicants()]
    return bcap.bcapResponse({
      'changed': True,
      'lastChange': reviewer.getLastChange(),
      'value': applicant_json
    })

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
    try:
      sc.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'invalid arguments'}
      return bcap.bcapResponse(resp)
    resp = {\
      'success' : True,\
      'name' : sc.name,\
      'shortform' : sc.shortform,\
    }
    return bcap.bcapResponse(resp)

class ScoreCategoryAddHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortform', 'maxval', 'minval']

  def name_str(self):
    return 'ScoreCategoryAddHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    name = args['name']
    shortform = args['shortform']
    maxval = args['maxval']
    minval = args['minval']
    
    sc = ScoreCategory(department=grantable.department, name=name, \
      shortform=shortform)
    try:
      sc.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'category already exists'}
      return bcap.bcapResponse(resp)

    value_range = range(int(minval), int(maxval) + 1)
    for x in value_range:
      sv = ScoreValue(category=sc, department=grantable.department, explanation='',\
        number=x)
      try:
        sv.save()
      except IntegrityError:
        resp = {'success' : False, 'message' : "couldn't create score value: " + str(x)}
        return bcap.bcapResponse(resp)

    resp = {\
      "success" : True,\
      "name" : name,\
      "shortform" : shortform,\
      "maxval" : maxval,\
      "minval" : minval,\
      "values" : [{'number' : v, 'explanation' : ''} for v in value_range]\
    }
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
    try:
      sv.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'invalid arguments'}
      return bcap.bcapResponse(resp)
    resp = {'success' : True}
    return bcap.bcapResponse(resp)

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
      shortform=shortform, autoemail=autoemail)
    try:
      position.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'position already exists'}
      return bcap.bcapResponse(resp)

    return bcap.bcapResponse({\
      'success' : True,\
      'name' : name,\
      'shortform' : shortform,\
      'autoemail' : autoemail})

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
    return bcap.bcapResponse({
      'name' : name,
      'abbr' : abbr,
      'success' : True,
      'delete' : delCap
    })

class AreaDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = Grant.objects.filter(db_entity=grantable)
    if len(grants) == 0:
      return logWith404(logger, 'ARDeleteHandler fatal error: no grant')
    area = grantable.area
    area.delete()
    return bcap.bcapNullResponse()

class UnverifiedApplicantAddHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def name_str(self):
    return 'UnverifiedApplicantAddHandler'

  def post(self, granted, args):
    posn = granted.applicantposition
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    email = args['email']
    uu = UnverifiedApplicant(email=email, department=posn.department, position=posn)

    try:
      uu.save()
    except:
      resp = {'success' : False, 'message' : 'failed to create UnverifiedApplicant'}
      return bcap.bcapResponse(resp)
    
    create_cap = bcap.grant('add-verified-applicant', uu)
    activate_url = '%s/new-account/#%s' % \
      (bcap.this_server_url_prefix(), create_cap.serialize())
    return_url = bcap.this_server_url_prefix()
    
    emailstr = u"""Dear Applicant,

A new Resume account is being created for you.  To activate it, visit:

%s

To regain access your account once it has been created, visit:

%s
"""
    emailstr = emailstr % (activate_url, return_url)
    sendLogEmail(emailstr, email)
    resp = {\
      'success' : True,\
      'email' : email,\
    }
    return bcap.bcapResponse(resp)

class UnverifiedUserAddRevHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email', 'role', 'name']

  def name_str(self):
    return 'UnverifiedUserAddRevHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    email = args['email']
    name = args['name']
    role = args['role']
    dept = grantable.department
    uu = UnverifiedUser(email=email, name=name, role=role, department=dept)
    try:
      uu.save()
    except:
      resp = {'success' : False, 'message' : 'failed to create UnverifiedUser'}
      return bcap.bcapResponse(resp)

    if role == 'admin': create_cap = bcap.grant('add-admin', uu)
    elif role == 'reviewer': create_cap = bcap.grant('add-reviewer', uu)
    else: return logWith404(logger, 'UnverifiedUserAddRevHandler: role type not allowed: %s' % role)

    activate_url = '%s/new-account/#%s' % \
      (bcap.this_server_url_prefix(), create_cap.serialize())
    return_url = bcap.this_server_url_prefix()
    
    emailstr = u"""Dear %s,

A new Resume account is being created for you.  To activate it, visit:

%s

To regain access your account once it has been created, visit:

%s
"""
    emailstr = emailstr % (name, activate_url, return_url)
    sendLogEmail(emailstr, email)

    resp = {\
      'success' : True,\
      'email' : email,\
      'name' : name,\
      'role' : role,\
    }
    return bcap.bcapResponse(resp)

class UnverifiedUserDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = Grant.objects.filter(db_entity=grantable)
    if len(grants) == 0:
      return logWith404(logger, 'UnverifiedUserDeleteHandler fatal error: no grant')
    uu = grantable.unverifieduser
    uu.delete()
    return bcap.bcapNullResponse()

class UnverifiedUserGetPendingHandler(bcap.CapHandler):
  def get(self, grantable):
    pending = grantable.department.getPending()
    result = [\
        {'name' : u.name,\
         'role' : u.role,\
         'email' : u.email,\
         'del' : bcap.grant('unverifieduser-delete', u)\
        } for u in pending]
    return bcap.bcapResponse(result)

class GetReviewersHandler(bcap.CapHandler):
  def get(self, grantable):
    reviewers = grantable.department.getReviewers()
    return bcap.bcapResponse(reviewers)

class ChangeContactsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['contactName', 'contactEmail', 'techEmail']

  def name_str(self):
    return 'ChangeContactsHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    dept = grantable.department
    dept.contactName = args['contactName']
    dept.contactEmail = args['contactEmail']
    dept.techEmail = args['techEmail']
    try:
      dept.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'invalid arguments'}
      return bcap.bcapResponse(resp)

    resp = {'success' : True}
    return bcap.bcapResponse(resp)

class FindRefsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def name_str(self):
    return 'FindRefsHandler'

  def post(self, grantable, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    refs = grantable.department.findRefs(args['email'])
    return bcap.bcapResponse(refs)

class GetBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic_info = granted.department.getBasic()
    response_areas = [\
      {'name' : a.name,\
       'abbr' : a.abbr,\
       'del' : bcap.grant('area-delete', a)\
      } for a in basic_info['areas']]
    basic_info['areas'] = response_areas
    response_scores = [\
      {'name' : s.name,\
       'shortform' : s.shortform,\
       'values' : [\
          {'number' : v.number,\
           'explanation' : v.explanation,\
           'change' : bcap.grant('scorevalue-change', v)} for v in s.getValues()],\
       'del' : bcap.grant('scorecategory-delete', s),\
       'change' : bcap.grant('scorecategory-change', s)\
      } for s in basic_info['scores']]
    basic_info['scores'] = response_scores
    return bcap.bcapResponse(basic_info)

class SetBasicHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortname', 'lastChange', 'brandColor', 'contactName',\
      'contactEmail', 'techEmail']

  def name_str(self):
    return 'SetBasicHandler'

  def post(self, granted, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response

    dept = granted.department
    dept.name = args['name']
    dept.shortname = args['shortname']
    dept.lastChange = args['lastChange']
    dept.brandColor = args['brandColor']
    dept.contactName = args['contactName']
    dept.contactEmail = args['contactEmail']
    dept.techEmail = args['techEmail']

    try:
      dept.save()
    except IntegrityError:
      resp = {'success' : False, 'message' : 'invalid arguments'}
      return bcap.bcapResponse(resp)

    resp = {'success' : True}
    return bcap.bcapResponse(resp)

class GetCSVHandler(bcap.CapHandler):
  def get(self, granted):
    return logWith404(logger, 'GetCSVHandler NYI')
