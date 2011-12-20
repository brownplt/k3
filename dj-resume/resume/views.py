import os
import logging
import random
import uuid

import smtplib

import settings
from resume.models import *
import belaylibs.dj_belay as bcap
from lib.py.common import logWith404
from belaylibs.models import Grant

from django.core.validators import validate_email
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpRequest, HttpResponseNotFound, HttpResponseServerError
from django.core.mail import send_mail
from django.db import IntegrityError

logger = logging.getLogger('default')

class FileUploadException(Exception):
  pass

def get_file_type(contents):
  if contents[0:4] == '%PDF':
    return 'pdf'
  elif contents[0:8] == '\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
    return 'doc'
  elif contents[0:8] == '\x50\x4b\x03\x04\x14\x00\x06\x00':
    return 'docx'
  else:
    return 'unknown'

def get_letter_filename(reference):
  return 'letter-%d-%d' % (reference.applicant.id, reference.id)

def get_statement_filename(applicant, component_type):
  return '%d-%d' % (applicant.id,component_type.id)

def save_file(f, filename):
  contents = f.read()
  file_type = get_file_type(contents)
  if file_type is 'unknown':
    raise FileUploadException('The file you uploaded is neither a PDF nor a Word document.')

  if not os.path.exists(settings.SAVEDFILES_DIR):
    raise Exception(\
      'directory specified by settings.SAVEDFILES_DIR does not exist: %s'\
      % settings.SAVEDFILES_DIR)

  path = os.path.join(settings.SAVEDFILES_DIR, filename)
  try:
    os.remove(path)
  except OSError,e:
    pass

  target = open(path, 'w')
  target.write(contents) 
  target.close()

def notFoundResponse():
  message = 'We didn\'t recognize that email address.  Please check what you \
 entered and try again.'

  return bcap.bcapResponse({
    'emailError': True,
    'error': message,
    'message': message
  })

def emailErrorResponse():
  message = 'We had trouble sending your message.  If this problem \
persists, contact the system maintainer.'

  return bcap.bcapResponse({
    'emailError': True,
    'error': message,
    'message': message
  })

# TODO: exceptions
def sendLogEmail(subject, msg, address, fromaddr):
  try:
    validate_email(address)
  except Exception as e:
    logger.error('Couldn\'t send email (bad address): %s' % e)
    return notFoundResponse()
  logger.info('Trying to send e-mail')
  if settings.DEBUG:
    logger.error('send log email:\n %s (From: %s) \n %s \n%s' % (subject, fromaddr, address, msg))
    return False
  try:
    send_mail(subject, msg, fromaddr, [address], fail_silently=False)
  except smtplib.SMTPRecipientsRefused as e:
    logger.error('Couldn\'t send email (refused): %s' % e)
    return notFoundResponse()
  except Exception as e:
    logger.error('Couldn\'t send email (unknown): %s' % e)
    return emailErrorResponse()
  logger.error('Sent real email:\n %s \n%s' % (address, msg))
  return False


def make_index_handler(index_file, dept_name):
  def index_handler(request):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['GET'])

    try:
      logger.info('Dept: %s' % dept_name)
      dept = Department.departmentByName(dept_name)
      cap = bcap.grant('add-applicant', dept)
    except Exception as e:
      return logWith404(logger, "Looked up bad department: %s, %s" % (dept_name, e), level='error')
    return render_to_response(index_file, {
      'create_applicant': cap.serialize(),
      'contact': dept.shortname
    })

  return index_handler

cs_index_handler = make_index_handler('index.html','cs')
bhort_index_handler = make_index_handler('index.html','bhort')
new_applicant_handler = make_index_handler('new-applicant.html','cs')
new_account_handler = make_index_handler('new_account.html', 'cs')

def make_contact_handler(dept_name):
  def contact_handler(request):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['GET'])

    try:
      logger.info('Contact: %s' % dept_name)
      dept = Department.departmentByName(dept_name)
    except Exception as e:
      return logWith404(logger, "Looked up bad department: %s, %s" % (dept_name, e), level='error')
    return render_to_response('contact.html', {
      'tech_contact': dept.techEmail,
      'admin_name': dept.contactName,
      'admin_email': dept.contactEmail
    })
  
  return contact_handler

cs_contact_handler = make_contact_handler('cs')
bhort_contact_handler = make_contact_handler('bhort')

def index_handler(request):
  if (request.method != 'GET'):
    return HttpResponseNotAllowed(['GET'])
  return render_to_response('coming-soon.html', { })

def make_get_handler(template):
  def handler(request):
    if request.method != 'GET':
      return HttpResponseNotAllowed(['GET'])

    return render_to_response(template, {})
  return handler

appreview_handler = make_get_handler('appreview.html')
reference_handler = make_get_handler('reference.html')
review_handler = make_get_handler('review.html')
admin_handler = make_get_handler('admin.html')
applicant_handler = make_get_handler('application.html')
contact_handler = make_get_handler('contact.html')

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
        'stash-applicant' : ApplicantStashHandler,\
        'update-applicant-name' : ApplicantUpdateNameHandler,\
        'launch-app-review' : LaunchAppReviewHandler,\
        'get-app-review' : GetAppReviewHandler,\
        'unverifieduser-addrev' : UnverifiedUserAddRevHandler, 
        'unverifieduser-delete' : UnverifiedUserDeleteHandler,
        'unverifieduser-getpending' : UnverifiedUserGetPendingHandler,
        'get-reviewers' : GetReviewersHandler,
        'appreview-get-reviewers' : AppReviewGetReviewersHandler,\
        'change-contacts' : ChangeContactsHandler,\
        'find-refs' : FindRefsHandler,\
        'find-applicant' : FindApplicantHandler,\
        'get-basic' : GetBasicHandler,\
        'get-applicant-basic' : GetApplicantBasicHandler,\
        'set-basic' : SetBasicHandler,\
        'get-reviewer' : GetReviewerHandler,\
        'get-applicants' : GetApplicantsHandler,\
        'add-applicant-with-position' : UnverifiedApplicantAddHandler,\
        'add-verified-applicant' : AddVerifiedApplicantHandler,\
        'get-applicant-email-and-create' : ApplicantEmailAndCreateHandler,\
        'get-reviewer-email-and-create' : ReviewerEmailAndCreateHandler,\
        'get-admin-email-and-create' : AdminEmailAndCreateHandler,\
        'request-reference' : RequestReferenceHandler,\
        'remind-reference' : RemindReferenceHandler,\
        'launch-reference' : LaunchReferenceHandler,\
        'reference-letter' : ReferenceLetterHandler,\
        'submit-contact-info' : SubmitContactInfoHandler,\
        'contact-info' : ContactHandler,
        'get-applicant' : GetApplicantHandler,\
        'applicant-ready' : ApplicantReadyHandler,\
        'apprev-get-applicant' : AppReviewGetApplicantHandler,\
        'submit-statement' : SubmitStatementHandler,\
        'get-review' : GetReviewHandler,\
        'change-applicant' : ChangeApplicantHandler,\
        'set-position' : SetPositionHandler,\
        'get-statement' : GetStatementHandler,\
        'get-letter' : GetLetterHandler,\
        'get-combined' : GetCombinedHandler,\
        'upload-material' : UploadMaterialHandler,\
        'revert-review' : RevertReviewHandler,\
        'submit-review' : SubmitReviewHandler,\
        'highlight-applicant' : HighlightApplicantHandler,\
        'unhighlight-applicant' : UnhighlightApplicantHandler,\
        'get-highlight-status' : GetHighlightStatusHandler,\
        'reject-applicant' : RejectApplicantHandler,\
        'hide-applicant' : HideApplicantHandler,\
        'set-areas' : SetAreasHandler,\
        'get-csv' : GetCSVHandler })
    return None

class ApplicantEmailAndCreateHandler(bcap.CapHandler):
  # granted: UnverifiedApplicant
  def get(self, granted):
    ua = granted.unverifiedapplicant
    email = ua.email
    create_cap = bcap.regrant('add-verified-applicant', ua)
    return bcap.bcapResponse({
      'email': email,
      'create': create_cap,
    })

class AdminEmailAndCreateHandler(bcap.CapHandler):
  # granted: UnverifiedUser
  def get(self, granted):
    uu = granted.unverifieduser
    email = uu.email
    create_cap = bcap.regrant('add-admin', uu)
    response = {
      'email': email,
      'create': create_cap
    }
    maybeBelayAccount = uu.belay_account()
    if maybeBelayAccount:
      response['createBelay'] = maybeBelayAccount
    return bcap.bcapResponse(response)

class ReviewerEmailAndCreateHandler(bcap.CapHandler):
  # granted: UnverifiedUser
  def get(self, granted):
    uu = granted.unverifieduser
    email = uu.email
    create_cap = bcap.regrant('add-reviewer', uu)
    response = {
      'email': email,
      'create': create_cap
    }
    maybeBelayAccount = uu.belay_account()
    if maybeBelayAccount:
      response['createBelay'] = maybeBelayAccount
    return bcap.bcapResponse(response)

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
      'findApplicant' : bcap.grant('find-applicant', department),\
      'changeContacts' : bcap.grant('change-contacts', department),\
      'getCSV' : bcap.grant('get-csv', department)\
    }
    return bcap.bcapResponse(resp)

class ApplicantLaunchHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    department = applicant.department
    references = applicant.getReferencesModel()
    reminders = { }
    for r in references:
      reminders[r.email] = bcap.regrant('remind-reference', r)

    resp = {\
      'getBasic' : bcap.grant('get-applicant-basic', department),\
      'reminders' : reminders,
      'requestReference' : bcap.grant('request-reference', applicant),\
      'submitContactInfo' : bcap.grant('submit-contact-info', applicant),\
      'submitStatement' : bcap.grant('submit-statement', applicant),\
      'setReady' : bcap.grant('applicant-ready', applicant),\
      'updateName' : bcap.grant('update-applicant-name', applicant),\
      'get' : bcap.grant('get-applicant', applicant)\
    }
    return bcap.bcapResponse(resp)

class RemindReferenceHandler(bcap.CapHandler):
  def post_arg_names(self): return []

  def post(self, grantable, args):
    reference = grantable.reference
    sendReferenceRequest(reference.applicant, reference)
    return bcap.bcapResponse({ 'success' : True })


class ApplicantReadyHandler(bcap.CapHandler):
  def post_arg_names(self): return ['ready']

  def post(self, grantable, args):
    applicant = grantable.applicant
    applicant.setReady(args['ready'])
    return bcap.bcapResponse({ 'ready' : applicant.getReady() })

class ApplicantUpdateNameHandler(bcap.CapHandler):
  def post(self, granted, args):
    applicant = granted.applicant
    if args.has_key('firstname'):
      applicant.firstname = args['firstname']
    if args.has_key('lastname'):
      applicant.lastname = args['lastname']
    try:
      applicant.save()
    except IntegrityError:
      return logWith404(logger, "failed to update applicant name: %s %s"\
        % (applicant.firstname, applicant.lastname), level='error')
    return bcap.bcapResponse({\
      'firstname' : applicant.firstname,\
      'lastname' : applicant.lastname,\
    })

def sendReferenceConfirmation(ref):
  message = """Dear %(refname)s,

This message confirms that the %(orgname)s received your letter of reference for %(appname)s.

Thanks!
%(orgname)s

If you received this message in error, please reply to this email to let us know.
""" % { 'orgname' : ref.department.name,
        'appname' : ref.applicant.fullname(),
        'refname' : ref.name }

  subject = "%s Reference Confirmation (%s)" % (ref.department.name, ref.applicant.fullname())

  fromaddr = fromAddr(ref.department)
  emailResponse = sendLogEmail(subject, message, ref.email, fromaddr)

  if emailResponse: return emailResponse
  return {'success' : True}
  
class ReferenceLetterHandler(bcap.CapHandler):
  def files_needed(self):
    return ['letter']

  def post_arg_names(self):
    return []

  def post_files(self, granted, args, files):

    reference = granted.reference
    letter = files['letter']
    filename = 'letter-%d-%d' % (reference.applicant.id, reference.id)

    try:
      save_file(letter, 'letter-%d-%d' % (reference.applicant.id, reference.id))
    except FileUploadException as e:
      msg = str(e)
      logger.info('submit-reference FileUploadException: %s' % msg)
      return bcap.bcapResponse({'error' : msg})
    except Exception as e:
      return logWith404(logger, 'save_file exception: %s' % e)

    reference.submitted = int(time.time())
    reference.filename = filename
    reference.filesize = len(letter)
    reference.save()

    sendReferenceConfirmation(reference)

    resp = reference.to_json()
    resp['appname'] = reference.applicant.to_json()

    return bcap.bcapResponse(resp)

class LaunchReferenceHandler(bcap.CapHandler):
  def get(self, granted):
    ref = granted.reference
    launch_info = ref.to_json()
    letter = bcap.grant('reference-letter', ref)
    launch_info['currentLetter'] = letter
    launch_info['appname'] = ref.applicant.fullname()
    launch_info['contact'] = ref.department.shortname

    return bcap.bcapResponse(launch_info)


def makeReferenceRequest(applicant, ref, launch_cap, orgname, shortname):
  return u"""Dear %(name)s,

%(appname)s has requested that you provide a letter of reference to the %(orgname)s.

To submit your letter, please visit this URL:

%(servername)s/submit-reference/#%(launch_cap)s

You can revisit this URL any number of times to resubmit your letter for %(appname)s.
	
If you run into any trouble, get help here:

%(servername)s/contact/%(shortname)s

Thanks!
%(orgname)s
""" % {
          'appname'    : applicant.fullname(),
          'name'       : ref.name,
          'launch_cap' : launch_cap.serialize(),
          'servername' : bcap.this_server_url_prefix(),
          'orgname'    : orgname,
          'shortname'  : shortname
        }

def fromAddr(dept):
  return '%s <%s>' % (dept.contactName, dept.contactEmail)

def sendReferenceRequest(applicant, ref):
  launch_cap = bcap.grant('launch-reference', ref)
  orgname = applicant.department.name
  shortname = applicant.department.shortname
  fromaddr = fromAddr(applicant.department)
  message = makeReferenceRequest(applicant, ref, launch_cap, orgname, shortname)
  subject = "%s Reference Request (%s)" % (orgname, applicant.fullname())
  emailResponse = sendLogEmail(subject, message, ref.email, fromaddr)
  if emailResponse: return {'error': emailResponse}
  return {'success': launch_cap}

class RequestReferenceHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'institution', 'email']

  def name_str(self):
    return 'RequestReferenceHandler'

  def exceptionResponse(self, msg):
    return bcap.bcapResponse({'success' : False, 'error' : msg})

  def post(self, granted, args):
    response = self.checkPostArgs(args)
    if response != 'OK':
      return response
    email = args['email']
    name = args['name']
    institution = args['institution']

    applicant = granted.applicant
    found = applicant.getReferencesOfEmail(email)
    if len(found) > 0:
      return self.exceptionResponse('You have already asked this person to write you a letter. If you wish to contact this person, please do so outside the Resume system.')
    if name == '':
      return self.exceptionResponse('No name was provided, please provide a name for the letter writer')
    if email == '':
      return self.exceptionResponse('No email was provided, please provide an email for the reference request')

    ref = Reference(applicant=applicant, submitted=0, filesize=0,\
      name=name, institution=institution, email=email,\
      department=applicant.department)
    ref.save()
    if applicant.position.autoemail:
      sendResponse = sendReferenceRequest(applicant, ref)
      if 'error' in sendResponse:
        return sendResponse['error']
    resp = ref.to_json()
    resp['reminder'] = bcap.regrant('remind-reference', ref)
    return bcap.bcapResponse(resp)

class SubmitContactInfoHandler(bcap.CapHandler):
  def post(self, granted, args):
    applicant = granted.applicant
    for (key, val) in args.iteritems():
      if key == 'comp-firstname':
        applicant.firstname = val
        applicant.save()
      elif key == 'comp-lastname':
        applicant.lastname = val
        applicant.save()
      elif key == 'comp-gender':
        applicant.gender = val
        applicant.save()
      elif key == 'comp-ethname':
        applicant.ethnicity = val
        applicant.save()
      elif key.find('comp-') == 0:
        id = key[5:]
        applicant.componentUpdate(id, val)
    return bcap.bcapResponse({'success' : True})

class GetApplicantHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    return bcap.bcapResponse(applicant.to_json())

class AppReviewGetApplicantHandler(bcap.CapHandler):
  def get(self, granted):
    pair = granted.apprevpair
    a_json = pair.applicant.to_json()
    references = pair.applicant.getReferencesModel()
    refjson = []
    for r in references:
      rjson = r.to_json()
      rjson['getLetter'] = bcap.regrant('get-letter', r)
      refjson.append(rjson)
    a_json['refletters'] = refjson

    return bcap.bcapResponse(a_json)

class GetHighlightStatusHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(len(granted.apprevpair.get_highlights()) > 0)

class SubmitStatementHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['comp']

  def name_str(self):
    return 'SubmitStatementHandler'

  def files_needed(self):
    return ['statement']

  def post_files(self, granted, args, files):
    applicant = granted.applicant
    statement = files['statement']
    cid = int(args['comp'])
    cts = applicant.getComponentTypeById(cid)
    if len(cts) == 0:
      return logWith404(logger, 'no component type by id = %s' % cid, level='error')
    ct = cts[0]

    try:
      save_file(statement, get_statement_filename(applicant, ct))
    except FileUploadException as e:
      msg = str(e)
      logger.info('submit-statement FileUploadException: %s' % msg)
      return bcap.bcapResponse({'error' : msg})
    except Exception as e:
      return logWith404(logger, 'save_file exception: %s' % e)

    components = applicant.getComponentByType(ct)
    if len(components) > 0:
      component = components[0]
    else:
      component = Component(applicant=applicant, type=ct, value='',\
        department=applicant.department)
    component.lastSubmitted = int(time.time())
    component.value = statement.size
    component.save()

    app_info = applicant.to_json()

    resp = {'component' : ct.name, 'app' : app_info}
    return bcap.bcapResponse(resp)

class AddVerifiedApplicantHandler(bcap.CapHandler):
  def post(self, granted, args):
    if granted is None:
      return HttpResponseNotFound()
    ua = granted.unverifiedapplicant

    auth_info = AuthInfo(
      email=ua.email, \
      # TODO(matt): fix or remove name from AuthInfo?
      name='',\
      role='applicant', \
      department=ua.department)
    auth_info.save()

    applicant = Applicant(\
      auth = auth_info,\
      firstname='',\
      lastname='',\
      country='',\
      department=ua.department,\
      position=ua.position\
    )
    applicant.save()

    ua.delete()
    launch = bcap.grant('launch-applicant', applicant)
    return bcap.bcapResponse({
      'public_data': 'Edit application for %s' % ua.email,
      'private_data': launch,
      'domain': bcap.this_server_url_prefix(),
      'url': '/applicant/'
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
      'url': '/admin/'
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
      'getApplicants': bcap.regrant('get-applicants', granted),
      'numApplicants': Applicant.objects.filter(
        department=granted.reviewer.department
      ).count()
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


class LaunchAppReviewHandler(bcap.CapHandler):
  def get(self, granted):
    pair = granted.apprevpair
    applicant = pair.applicant
    
    components = applicant.get_component_objects()
    component_caps = dict(\
      [(c.type.id, bcap.grant('get-statement', c))\
      for c in components if c.type.type == 'statement'])

    resp = {\
      'getBasic' : bcap.grant('get-basic', applicant.department),\
      'getApplicant' : bcap.grant('apprev-get-applicant', pair),\
      'getReviewers' : bcap.grant('appreview-get-reviewers', applicant),\
      'getReview' : bcap.grant('get-review', pair),\
      'setAreas' : bcap.grant('set-areas', applicant),\
      # setGender/Ethnicity mapped to changeApplicant
      'changeApplicant' : bcap.grant('change-applicant', applicant),\
      'setPosition' : bcap.grant('set-position', applicant),\
      'componentCaps' : component_caps,\
      'getCombined' : bcap.grant('get-combined', applicant),\
      'uploadMaterial' : bcap.grant('upload-material', applicant),\
      'revertReview' : bcap.grant('revert-review', pair),\
      'submitReview' : bcap.grant('submit-review', pair),\
      'getHighlightStatus' : bcap.grant('get-highlight-status', pair),\
      'unhighlightApplicant' : bcap.grant('unhighlight-applicant', pair),\
      'rejectApplicant' : bcap.grant('reject-applicant', applicant),\
      'hideApplicant' : bcap.grant('hide-applicant', pair),\
    }
    return bcap.bcapResponse(resp)

class GetReviewHandler(bcap.CapHandler):
  def get(self, granted):
    pair = granted.apprevpair
    drafts = pair.get_reviews(draft=True)
    if len(drafts) == 0:
      return bcap.bcapResponse(False)
    draft = drafts[0]
    return bcap.bcapResponse(draft.to_json())

class SetAreasHandler(bcap.CapHandler):
  # TODO(matt): duplication of functionality in SubmitReviewHandler,
  # should be refactored
  def post(self, granted, args):
    applicant = granted.applicant
    if not args.has_key('areas'):
      areas = {}
    else:
      areas = args['areas']

    for (aid, weight) in areas.iteritems():
      ar = applicant.department.get_area_by_id(aid)
      if weight == 'none':
        applicant.remove_area(ar)
      else:
        applicant.update_area(ar, weight)

    return bcap.bcapResponse(applicant.to_json())

class ChangeApplicantHandler(bcap.CapHandler):
  def name_str(self):
    return 'ChangeApplicantHandler'
  def post(self, granted, args):
    applicant = granted.applicant
    if args.has_key('gender'):
      applicant.gender = args['gender']
    if args.has_key('ethnicity'):
      applicant.ethnicity = args['ethnicity']
    applicant.save()
    return bcap.bcapResponse(applicant.to_json())

class SetPositionHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['id']
  def name_str(self):
    return 'SetPositionHandler'
  def post(self, granted, args):
    applicant = granted.applicant
    id = args['id']
    position = applicant.department.get_position_by_id(args['id'])
    if position:
      applicant.position = position
      applicant.save()
      return bcap.bcapResponse(applicant.to_json())
    return logWith404(logger, 'SetPositionHandler: no position with id %s' % id,\
      level='error')

def file_response(filename, response_prefix):
    full_path = os.path.join(settings.SAVEDFILES_DIR, filename)

    try:
      full_file = open(full_path, 'r')
      file_data = full_file.read()
    except Exception as e:
      return logWith404(logger,\
        'file_response: exception reading file: %s' % e,\
        level='error')

    file_type = get_file_type(file_data)
    if file_type == 'unknown':
      return logWith404(logger,\
        'GetStatementHandler: unknown statement file type',\
        level='error')
    elif file_type == 'pdf':
      mimetype = 'application/pdf'
    else:
      mimetype = 'application/msword'

    response = HttpResponse(file_data, mimetype=mimetype)
    resp_filename = '%s.%s' % (\
      response_prefix,\
      file_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % resp_filename
    return response

class GetLetterHandler(bcap.CapHandler):
  def get(self, granted):
    ref = granted.reference
    filename = get_letter_filename(ref)
    return file_response(filename, 'letter')

class GetStatementHandler(bcap.CapHandler):
  def get(self, granted):
    component = granted.component
    filename = get_statement_filename(component.applicant, component.type)
    statement_path = os.path.join(settings.SAVEDFILES_DIR, filename)

    try:
      statement_file = open(statement_path, 'r')
      statement_data = statement_file.read()
    except Exception as e:
      return logWith404(logger,\
        'GetStatementHandler: exception reading file: %s' % e,\
        level='error')

    file_type = get_file_type(statement_data)
    if file_type == 'unknown':
      return logWith404(logger,\
        'GetStatementHandler: unknown statement file type',\
        level='error')
    elif file_type == 'pdf':
      mimetype = 'application/pdf'
    else:
      mimetype = 'application/msword'

    response = HttpResponse(statement_data, mimetype=mimetype)
    resp_filename = 'applicant_%s.%s' % (\
      component.type.name.replace(' ', '_'),\
      file_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % resp_filename
    return response

class GetCombinedHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    try:
      from lib.py.combiner import get_combined_data
      combined_data = get_combined_data(applicant)
      response = HttpResponse(combined_data, mimetype='pdf')
      response['Content-Disposition'] = 'attachment; filename=applicant_combined.pdf'
      return response
    except Exception as e:
      return logWith404(logger, 'GetCombinedHandler: %s' % e, level='error')

class UploadMaterialHandler(bcap.CapHandler):
  def name_str(self):
    return 'UploadMaterialHandler'
  def post(self, granted, args):
    applicant = granted.applicant
    return logWith404(logger, 'UploadMaterialHandler NYI')

class RevertReviewHandler(bcap.CapHandler):
  def name_str(self):
    return 'RevertReviewHandler'
  def post(self, granted, args):
    pair = granted.apprevpair
    drafts = pair.get_reviews(True)
    subs = pair.get_reviews(False)
    if len(drafts) > 0 and len(subs) > 0:
      draft = drafts[0]
      sub = subs[0]
      draft.destroy_scores()
      draft.transfer_scores_from(sub)
      draft.comments = sub.comments
      draft.advocate = sub.advocate
      draft.save()
      return bcap.bcapResponse(draft.to_json())
    if len(drafts) > 0:
      draft = drafts[0]
      draft.delete()
    return bcap.bcapResponse('false')

class SubmitReviewHandler(bcap.CapHandler):
  def name_str(self):
    return 'SubmitReviewHandler'
  def post_arg_names(self):
    return ['draft', 'advdet', 'comments']
  def convert_scores_argument(self, scores):
    if scores == '':
      scores = []
    if not isinstance(scores, list):
      scores = [scores]
    return [int(s) for s in scores]
  def process_scoreval_ids(self, review, scores):
    # TODO(matt): this is the wrong way to do it, but the frontend is written
    # to pass ScoreValue IDs back and forth
    maybe_scores = [(val_id, review.get_new_score(val_id)) for val_id in scores]
    scores = filter(lambda s: not(s[1] is None), maybe_scores)
    errors = filter(lambda s: s[1] is None, maybe_scores)
    for (val_id, new_score) in scores:
      new_score.save() 
    for (val_id, none) in errors:
      logger.error('SubmitReviewHandler: no score value with id %s'\
        % str(val_id))
  def fillReview(self, scores, advdet, comments, pair, draft):
    reviews = pair.get_reviews(draft=draft)
    if len(reviews) > 0:
      review = reviews[0]
      review.comments = comments
      review.advocate = str(advdet)
    else:
      review = Review(department=pair.applicant.department,\
        applicant=pair.applicant, reviewer=pair.reviewer, comments=comments,\
        advocate=str(advdet), draft=draft)
    review.destroy_scores()
    review.save()
    self.process_scoreval_ids(review, scores)
  def post(self, granted, args):
    pair = granted.apprevpair
    draft = args['draft']
    advdet = args['advdet']
    comments = args['comments']
    if not args.has_key('scores'):
      scores = []
    else:
      scores = args['scores']
    scores = self.convert_scores_argument(scores)
    self.fillReview(scores, advdet, comments, pair, draft)
    return bcap.bcapResponse(pair.applicant.to_json())

class HighlightApplicantHandler(bcap.CapHandler):
  def post(self, granted, args):
    pair = granted.apprevpair
    highlights = pair.get_highlights()
    if len(highlights) == 0:
      h = Highlight(department=pair.applicant.department,\
        applicant=pair.applicant, highlightee=pair.reviewer)
      h.save()
    return bcap.bcapResponse(pair.applicant.to_json())

class UnhighlightApplicantHandler(bcap.CapHandler):
  def post(self, granted, args):
    pair = granted.apprevpair
    highlights = pair.get_highlights()
    highlights.delete()
    return bcap.bcapResponse(pair.applicant.to_json())

class RejectApplicantHandler(bcap.CapHandler):
  def post(self, granted, args):
    applicant = granted.applicant
    return logWith404(logger, 'RejectApplicantHandler NYI')

class HideApplicantHandler(bcap.CapHandler):
  def name_str(self):
    return 'HideApplicantHandler'
  def post_arg_names(self):
    return ['hide']
  def post(self, granted, args):
    pair = granted.apprevpair
    applicant = pair.applicant
    reviewer = pair.reviewer
    hide = args['hide']
    if hide == 'no':
      if applicant.is_hidden_from(reviewer):
        applicant.unhide_from(reviewer)
    elif hide == 'yes':
      if not applicant.is_hidden_from(reviewer):
        applicant.hide_from(reviewer)
    return bcap.bcapResponse(applicant.to_json())

class GetAppReviewHandler(bcap.CapHandler):
  def get(self, granted):
    applicant = granted.applicant
    return bcap.bcapResponse({
      'public_data' : 'Applicant review page for %s' % applicant.fullname(),
      'private_data' : bcap.regrant('launch-app-review', applicant),
      'domain': bcap.this_server_url_prefix(),
      'url' : '/appreview',
    })

class GetApplicantsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['lastChange']

  def post(self, grantable, args):
    reviewer = grantable.reviewer
    applicant_json = []
    for applicant in reviewer.getApplicants():
      pairs = applicant.getPairsOfReviewer(reviewer)
      if len(pairs) > 0:
        pair = pairs[0]
      else:
        pair = AppRevPair(applicant=applicant, reviewer=reviewer)
        pair.save()
      a_json = applicant.to_json()
      launchCap = bcap.cachegrant('launch-app-review', pair)
      a_json['launchURL'] = '%s/appreview/#%s' % \
           (bcap.this_server_url_prefix(), launchCap.serialize())
      components = applicant.get_component_objects()
      component_caps = dict(\
        [(c.type.id, bcap.cachegrant('get-statement', c))\
        for c in components if c.type.type == 'statement'])
      a_json['components'] = component_caps
      references = applicant.getReferencesModel()
      refjson = []
      for r in references:
        rjson = r.to_json()
        rjson['getLetter'] = bcap.cachegrant('get-letter', r)
        refjson.append(rjson)
      a_json['refletters'] = refjson
      applicant_json.append(a_json)
      a_json['getCombined'] = bcap.cachegrant('get-combined', applicant)
    return bcap.bcapResponse({
      'changed': True,
      'lastChange': reviewer.getLastChange(),
      'value': applicant_json
    })


class ScoreCategoryDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = grantable.my_grants()
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
    grants = grantable.my_grants()
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

    email = args['email']
    uu = UnverifiedApplicant(email=email, department=posn.department, position=posn)

    try:
      uu.save()
    except Exception as e:
      logger.error('Error: %s' % e)
      resp = {'success' : False, 'message' : 'failed to create UnverifiedApplicant'}
      return bcap.bcapResponse(resp)
    
    create_cap = bcap.grant('get-applicant-email-and-create', uu)
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
#    emailResponse = sendLogEmail('[Resume] New Account', emailstr, email)
#    if emailResponse: return emailResponse
    resp = {\
      'success' : True,\
      'email' : email,\
      'create_cap' : create_cap
    }
    return bcap.bcapResponse(resp)

class UnverifiedUserAddRevHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email', 'role', 'name']

  def name_str(self):
    return 'UnverifiedUserAddRevHandler'

  def post(self, grantable, args):

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

    create_belay = bcap.Capability(settings.BELAY_CREATE)
    response = create_belay.post(bcap.dataPreProcess({'email': args['email']}))
    logger.error('Successfully got response for account creation: %s' % response)
    create_cap = response['create']

    ub = UnverifiedBelayAccount(uu=uu, create=create_cap.serialize())
    ub.save()

    if role == 'admin': create_cap = bcap.grant('get-admin-email-and-create', uu)
    elif role == 'reviewer': create_cap = bcap.grant('get-reviewer-email-and-create', uu)
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
    
    fromaddr = fromAddr(dept)
    emailResponse = sendLogEmail('[Resume] New Account', emailstr, email, fromaddr)
    if emailResponse: return emailResponse
    resp = {\
      'success' : True,\
      'email' : email,\
      'name' : name,\
      'role' : role,\
    }
    return bcap.bcapResponse(resp)

class UnverifiedUserDeleteHandler(bcap.CapHandler):
  def delete(self, grantable):
    grants = grantable.my_grants()
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

class AppReviewGetReviewersHandler(bcap.CapHandler):
  """
  This handler differs from GetReviewersHandler in that it returns caps
  for highlighting the applicant.
  """
  def pair_of(self, applicant, reviewer):
    existing_pairs = applicant.getPairsOfReviewer(reviewer)
    if len(existing_pairs) > 0:
      return existing_pairs[0]
    new_pair = AppRevPair(applicant=applicant, reviewer=reviewer)
    new_pair.save()
    return new_pair
  def get(self, grantable):
    applicant = grantable.applicant
    reviewers = applicant.department.my(Reviewer)
    return bcap.bcapResponse([\
        { 'email' : r.auth.email,\
          'name' : r.auth.name,\
          'uname' : '%s (%s)' % (r.auth.name, r.auth.email),\
          'role' : r.auth.role,\
          'highlight' : bcap.grant('highlight-applicant', self.pair_of(applicant, r))\
        } for r in reviewers])

class ChangeContactsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['contactName', 'contactEmail', 'techEmail']

  def name_str(self):
    return 'ChangeContactsHandler'

  def post(self, grantable, args):

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


class ApplicantStashHandler(bcap.CapHandler):
  def get(self, grantable):
    launchCap = bcap.regrant('launch-applicant', grantable.applicant)

    return bcap.bcapResponse(launchCap)

class FindApplicantHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def name_str(self):
    return 'FindApplicantsHandler'

  def post(self, grantable, args):

    applicants = grantable.department.findApplicants(args['email'])
    apps = []
    for a in applicants:
      a_json = {}
      a_json['name'] = a.fullname()
      launchCap = bcap.regrant('stash-applicant', a)
      launchurl = '%s/applicant/#%s' % \
        (bcap.this_server_url_prefix(), launchCap.serialize())
      a_json['launch'] = launchurl
      apps.append(a_json)

    return bcap.bcapResponse(apps)

class FindRefsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def name_str(self):
    return 'FindRefsHandler'

  def post(self, grantable, args):

    refs = grantable.department.findRefs(args['email'])
    for r in refs:
      ref = r['reference']
      submitcap = bcap.regrant('launch-reference', ref)
      submitlink = '%s/submit-reference/#%s' % (bcap.this_server_url_prefix(), submitcap.serialize())
      r['submitlink'] = submitlink
      del r['reference']
      launchCap = bcap.regrant('stash-applicant', ref.applicant)
      launchurl = '%s/applicant/#%s' % \
        (bcap.this_server_url_prefix(), launchCap.serialize())
      r['launch'] = launchurl
    return bcap.bcapResponse(refs)

class ContactHandler(bcap.CapHandler):
  def get(self, granted):
    dept = granted.department
    return bcap.bcapResponse(dept.contact_json())

class GetApplicantBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic_info = granted.department.getBasic()
    basic_info['contact'] = granted.department.shortname
    return bcap.bcapResponse(basic_info)

class GetBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic_info = granted.department.getBasic()
    all_svals = granted.department.all_score_values()
    response_areas = [\
      {'name' : a.name,\
       'id' : a.id,\
       'abbr' : a.abbr,\
       'del' : bcap.grant('area-delete', a)\
      } for a in granted.department.my(Area)]
    basic_info['areas'] = response_areas
    basic_info['svcs'] = dict([(sv.id, sv.category.to_json()) for sv in all_svals])
    response_scores = [\
      {'name' : s.name,\
       'shortform' : s.shortform,\
       'values' : [\
       {'id' : v.id,\
         'number' : v.number,\
         'explanation' : v.explanation,\
         'change' : bcap.grant('scorevalue-change', v)} for v in s.getValues()],\
       'del' : bcap.grant('scorecategory-delete', s),\
       'id' : s.id,\
       'change' : bcap.grant('scorecategory-change', s)\
      } for s in granted.department.my(ScoreCategory)]
    basic_info['scores'] = response_scores
    basic_info['svnum'] = dict([(s.id, s.number) for s in all_svals])
    basic_info['contact'] = granted.department.shortname
    return bcap.bcapResponse(basic_info)

class SetBasicHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name', 'shortname', 'lastChange', 'brandColor', 'contactName',\
      'contactEmail', 'techEmail']

  def name_str(self):
    return 'SetBasicHandler'

  def post(self, granted, args):

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
