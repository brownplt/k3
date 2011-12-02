from django.shortcuts import redirect, render_to_response
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseNotFound, HttpRequest
from django.template.loader import render_to_string
from pltbelay.models import BelaySession, PltCredentials, GoogleCredentials, Stash, PendingLogin, PendingAccount
from xml.dom import minidom
import logging
import uuid
import urllib
import urllib2
from urlparse import urlparse
import hashlib

import smtplib

import belaylibs.dj_belay as bcap

from django.core.validators import validate_email
from django.core.mail import send_mail
from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string

from pltbelay.models import BelaySession, PltCredentials, BelayAccount
from lib.py.common import logWith404
import settings

logger = logging.getLogger('default')

class BelayInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'make-stash' : MakeStashHandler,
      'stash' : StashHandler,
      'create-account' : CreatePLTAccountHandler
    })
    return None

class StashHandler(bcap.CapHandler):
  def get(self, granted):
    stash = granted.stash
    return bcap.bcapResponse(bcap.dataPostProcess(stash.stashed_content))

  def put(self, granted, args):
    stash = granted.stash
    pd = bcap.dataPreProcess(args['private_data'])
    stash.stashed_content = pd
    stash.save()
    return bcap.bcapNullResponse()

  # TODO(joe): this isn't exactly what I want
  def post(self, granted, args):
    stash = Stash(stashed_content=bcap.dataPreProcess(args['private_data']))
    stash.save()
    stash_handler = bcap.grant('stash', stash)
    return bcap.bcapResponse(stash_handler)

  def delete(self, granted):
    granted.stash.delete()
    return bcap.bcapNullResponse()

class MakeStashHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['private_data']
  def post(self, granted, args):
    stash = Stash(stashed_content=bcap.dataPreProcess(args['private_data']))
    stash.save()
    stash_handler = bcap.grant('stash', stash)
    return bcap.bcapResponse(stash_handler)

def unameExists(uname):
  q = PltCredentials.objects.filter(username=uname)
  return len(q) == 1

HASH_ITERATIONS = 20
# TODO: non-ASCII characters can break this
# need to sanitize raw password
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.sha1()
    m1.update(salted)
    salted = m1.hexdigest()

  logging.debug("Salted: %s" % salted)
  return salted

# TODO(matt): restore instead of urlopen?
def newStationCap():
  generated = urllib2.urlopen(settings.STATION_DOMAIN + '/generate/')
  return bcap.dataPostProcess(generated.read())

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
    logger.error('Sending real email:\n %s (From: %s) \n %s \n%s' % (subject, fromaddr, address, msg))
    send_mail(subject, msg, fromaddr, [address], fail_silently=False)
  except smtplib.SMTPRecipientsRefused as e:
    logger.info('Couldn\'t send email (refused): %s' % e)
    return notFoundResponse()
  except Exception as e:
    logger.info('Couldn\'t send email (unknown): %s' % e)
    return emailErrorResponse()
  logger.info('Sent real email:\n %s \n%s' % (address, msg))
  return False

def request_plt_account(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  args = bcap.dataPostProcess(request.read())
  logger.info('request: %s' % args)
  if not args.has_key('email'):
    return logWith404(logger, 'request_account: post data missing email')

  pa = PendingAccount(email = args['email'])
  pa.save()
  create_cap = bcap.grant('create-account', pa)

  message = """
Hi!  You've requested an account with Resume at the Brown University Department of Computer Science.

Visit this link to get started:

%s/new-applicant/#%s
""" % (settings.APPURL, create_cap.serialize())

  emailResponse = sendLogEmail('Resume Account Request', message, args['email'], 'Lauren Clarke <lkc@cs.brown.edu>')
  if emailResponse: return emailResponse

  return bcap.bcapResponse({'success': True})

class CreatePLTAccountHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['username', 'password']

  def get(self, grantable):
    return bcap.bcapResponse(grantable.pendingaccount.email)

  def post(self, grantable, args):
    username = grantable.pendingaccount.email
    rawpassword = args['password']

    if len(username) > 200:
      return logWith404(logger, 'create_plt_account: bad username')

    if len(rawpassword) < 8:
      return logWith404(logger, 'create_plt_account: bad password')

    salt = str(uuid.uuid4())
    hashed_password = get_hashed(rawpassword, salt)

    station_cap = newStationCap()
    account = BelayAccount(station_url=station_cap.serialize())
    account.save()
    credentials = PltCredentials(username=username, \
      salt=salt, \
      hashed_password=hashed_password, \
      account=account)
    credentials.save()

    session_id = str(uuid.uuid4())

    session = BelaySession(session_id=session_id, account=account)
    session.save()

    grantable.pendingaccount.delete()

    response = {
      'station': station_cap,
      'makeStash': bcap.regrant('make-stash', account)
    }
    return bcap.bcapResponse(response)
    
   

def create_plt_account(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  if not args.has_key('username'):
    return logWith404(logger, 'create_plt_account: post data missing username')

  if not args.has_key('password'):
    return logWith404(logger, 'create_plt_account: post data missing password')

  username = args['username']
  rawpassword = args['password']

  if len(username) > 20:
    return logWith404(logger, 'create_plt_account: bad username')

  if len(rawpassword) < 8:
    return logWith404(logger, 'create_plt_account: bad password')

  salt = str(uuid.uuid4())
  hashed_password = get_hashed(rawpassword, salt)

  station_cap = newStationCap()
  account = BelayAccount(station_url=station_cap.serialize())
  account.save()
  credentials = PltCredentials(username=username, \
    salt=salt, \
    hashed_password=hashed_password, \
    account=account)
  credentials.save()

  session_id = str(uuid.uuid4())

  session = BelaySession(session_id=session_id, account=account)
  session.save()

  response = {
    'station': station_cap,
    'makeStash': bcap.regrant('make-stash', account)
  }
  return bcap.bcapResponse(response)

def plt_login(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  if not args.has_key('username'):
    return logWith404(logger, 'plt_login: post data missing username')
  if not args.has_key('password'):
    return logWith404(logger, 'plt_login: post data missing password')

  username = args['username']
  rawpassword = args['password']

  credentials = PltCredentials.objects.filter(username=username)
  if len(credentials) > 1:
    return logWith404(logger, 'plt_login: fatal error: duplicate credentials', level='error')

  if len(credentials) == 0:
    return bcap.bcapResponse({'loggedIn' : False})
  c = credentials[0]

  hashed_password = get_hashed(rawpassword, c.salt)
  if hashed_password != c.hashed_password:
    return bcap.bcapResponse({'loggedIn' : False})

  session_id = str(uuid.uuid4())
  session = BelaySession(session_id=session_id, account=c.account)
  session.save()

  response = {
    'station': bcap.Capability(c.account.station_url),
    'makeStash': bcap.regrant('make-stash', c.account)
  }
  return bcap.bcapResponse(response)

def glogin(request):
  if(request.method != 'GET'):
    logwith404(logger, "pltbelay: Tried to glogin with method: " % request.method)

  clientkey = str(request.GET['clientkey'])
  # I tried to use urllib.urlencode, but it translates slashes into escape
  # sequences
  def encode_for_get(param_obj):
    s = ""
    for nm in param_obj:
      s += nm + "=" + param_obj[nm] + "&"
    return s[:len(s)-1]

  f = urllib2.urlopen("https://www.google.com/accounts/o8/id")
  dom = minidom.parse(f)
  uris = dom.getElementsByTagName("URI")

  if len(uris) != 1:
    return HttpResponse("Error contacting Google OID endpoint", status=500)
  raw_uri = uris[0].firstChild.toxml()
  parsed = urlparse(raw_uri)

  pending = str(uuid.uuid4())
  pl = PendingLogin(key=pending, clientkey=clientkey)
  pl.save()

  param_obj = {
      'openid.ns' : 'http://specs.openid.net/auth/2.0',
      'openid.claimed_id' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.identity' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.return_to' : '%s/glogin_landing/%s' % (settings.SITE_NAME, pending),
      'openid.realm' : settings.SITE_NAME,
      'openid.mode' : 'checkid_setup',
      'openid.ns.ax' : 'http://openid.net/srv/ax/1.0',
      'openid.ax.mode' : 'fetch_request',
      'openid.ax.type.email' : 'http://axschema.org/contact/email',
      'openid.ax.required' : 'email'
  }
  params = encode_for_get(param_obj)

  req_url = ("https://" + parsed.netloc + parsed.path + "?%s") % params
  return redirect(req_url)

def check_pending(path_info):
  parts = path_info.split("/")
  try:
    pending = str(uuid.UUID(str(parts[-1])))
    logger.error(pending)
    pl = PendingLogin.objects.filter(key=pending)
    logger.error("Got something: %s, %s" % (pl, len(pl)))
    if len(pl) == 1:
      ret = pl[0].clientkey
      pl.delete()
      return ret
    else:
      logger.error('%s pendings.' % len(pl))
      return False
  except Exception as e:
    logger.error('Exception during pending processing: %s' % e)
    return False

def glogin_landing(request):
  if request.method == 'GET':
    d = request.GET
  else:
    d = request.POST
  maybe_client_key = check_pending(request.path_info)
  if not maybe_client_key:
    return logWith404(logger, "Bad pending: %s" % request.path_info, level='error')

  # 11.4.2 Verifying directly with the OpenID Provider
  # 11.4.2.1.  Request Parameters
  #   . openid.mode
  #         Value: "check_authentication"
  #   . Exact copies of all fields from the authentication response, except
  #     for "openid.mode".
  # http://openid.net/specs/openid-authentication-2_0.html#check_auth
  verify = {}
  for e in d:
    verify[e] = d[e]
  verify['openid.mode'] = 'check_authentication'

  try:
    f = urllib2.urlopen("https://www.google.com/accounts/o8/ud", urllib.urlencode(verify))
    beginning = str(f.read()[0:13]) 
    
    if(beginning != 'is_valid:true'):
      return bcap.bcapResponse('fail')
  except urllib2.HTTPError as e:
    logger.error("ErrorResponse: %s" % e.read())
    return bcap.bcapNullResponse()
    
  identity = d['openid.identity']
  email = d['openid.ext1.value.email']

  q = GoogleCredentials.objects.filter(identity=identity)
  if len(q) == 0:
    station_cap = newStationCap()
    account = BelayAccount(station_url=station_cap.serialize())
    account.save()

    gc = GoogleCredentials(account=account, identity=identity)
    gc.save()
  else:
    account = q[0].account

  session_id = str(uuid.uuid4())
  session = BelaySession(account=account, session_id=session_id)
  session.save()

  response = render_to_response('glogin.html', {
    'clientkey': maybe_client_key,
    'station': account.station_url,
    'make_stash': bcap.regrant('make-stash', account).serialize(),
    'site_name': settings.SITE_NAME,
    'email': email
  })
  return response

def check_uname(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  args = bcap.dataPostProcess(request.read())
  uname = args['username']
  available = not unameExists(uname)
  return bcap.bcapResponse({ "available" : available }) 

def check_login(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  response = {}

  if not ('session' in request.COOKIES):
    response['loggedIn'] = False
    return bcap.bcapResponse(response)

  if not (args.has_key('sessionID')):
    return logWith404(logger, "check_login: request didn't pass sessionID arg") 

  session_id = request.COOKIES['session']
  req_session_id = args['sessionID']
  if req_session_id != session_id:
    return logWith404(logger, "check_login: request session_id %s didn't match cookie\
        session_id %s" % (req_session_id, session_id))

  sessions = BelaySession.objects.filter(session_id=session_id)
  if len(sessions) > 1:
    return logWith404(logger, "check_login: fatal error, duplicate BelaySessions", level='error')

  response['loggedIn'] = (len(sessions) > 0)
  return bcap.bcapResponse(response)

def belay_frame(request):
  if (request.method != 'GET'):
    return HttpResponseNotAllowed(['GET'])

  return render_to_response('belay-frame.html', {
    'site_name' : settings.SITE_NAME
  })
