from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseNotFound, HttpRequest
from django.template.loader import render_to_string
from pltbelay.models import BelaySession, PltCredentials, GoogleCredentials, Stash
from xml.dom import minidom
import logging
import uuid
import hashlib
import httplib
import urllib
import urllib2
from urlparse import urlparse
import hashlib

import belaylibs.dj_belay as bcap

from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string

from pltbelay.models import BelaySession, PltCredentials, BelayAccount
import settings

logger = logging.getLogger('default')

class BelayInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {'get-stash' : GetStashHandler})
    return None

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

def unameExists(uname):
  q = PltCredentials.objects.filter(username=uname)
  logging.debug('checking')
  return len(q) == 1

HASH_ITERATIONS = 20
# TODO: non-ASCII characters can break this
# need to sanitize raw password
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.md5()
    m1.update(salted)
    salted = m1.hexdigest()

  logging.debug("Salted: %s" % salted)
  return salted

def accountForSession(session_id):
  q = BelaySession.objects.filter(session_id=session_id)

  if len(q) == 0:
    return None
  else:
    return q[0].account

def get_station(request):
  if not 'session' in request.COOKIES:
    logger.debug('Failed to find session')
    return HttpResponse(status=500)
    
  sid = request.COOKIES['session']
  acct = accountForSession(sid)

  return HttpResponse(acct.station_url)

# TODO(matt): restore instead of urlopen?
def newStationCap():
  generated = urllib2.urlopen(settings.STATION_DOMAIN + '/generate/')
  return bcap.dataPostProcess(generated.read())

def create_plt_account(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  if not args.has_key('username'):
    return logWith404('create_plt_account: post data missing username')

  if not args.has_key('password'):
    return logWith404('create_plt_account: post data missing password')

  username = args['username']
  rawpassword = args['password']

  if len(username) > 20:
    return logWith404('create_plt_account: bad username')

  if len(rawpassword) < 8:
    return logWith404('create_plt_account: bad password')

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

  response = HttpResponse()
  cstr = 'session=%s; expires=Sun,31-May-2040 23:59:59 GMT; path=/;' % session_id
  response['Set-Cookie'] = cstr

  redirect_url = '/static/belay-frame.html'
  content = bcap.dataPreProcess({ "redirectTo" : redirect_url })
  bcap.xhr_content(response, content, 'text/plain;charset=UTF-8')
  return response

# TODO : fix intermediate page (to get on google's domain)
def glogin(request):
  # I tried to use urllib.urlencode, but it translates slashes into escape sequences
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

  param_obj = {
      'openid.ns' : 'http://specs.openid.net/auth/2.0',
      'openid.claimed_id' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.identity' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.return_to' : '%s/glogin_landing/' % settings.SITE_NAME,
      'openid.realm' : settings.SITE_NAME,
      'openid.mode' : 'checkid_setup'
  }
  params = encode_for_get(param_obj)

  req_url = ("https://" + parsed.netloc + parsed.path + "?%s") % params
  f = urllib2.urlopen(req_url)
  return HttpResponse(f.read())

def glogin_landing(request):
  if request.method == 'GET':
    d = request.GET
  else:
    d = request.POST
  identity = d['openid.identity']

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

  response = HttpResponse('Success')
  cstr = 'session=%s; expires=Sun,31-May-2040 23:59:59 GMT; path=/;' % session_id
  response['Set-Cookie'] = cstr
  return response

def plt_login(request):
  return HttpResponse("PLT Login NYI", status=500)

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
    return logWith404("check_login: request didn't pass sessionID arg") 

  session_id = request.COOKIES['session']
  req_session_id = args['sessionID']
  if req_session_id != session_id:
    return logWith404("check_login: request session_id %s didn't match cookie\
        session_id %s" % (req_session_id, session_id))

  sessions = BelaySession.objects.filter(session_id=session_id)
  if len(sessions) > 1:
    return logWith404("check_login: fatal error, duplicate BelaySessions", level='warn')

  response['loggedIn'] = (len(sessions) > 0)
  return bcap.bcapResponse(response)

def make_stash(request):
  if not ('session' in request.COOKIES):
    return logWith404('make_stash: no session cookie')

  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])

  args = bcap.dataPostProcess(request.read())
  if not (args.has_key('sessionID')):
    return logWith404("make_stash: request didn't pass sessionID arg")
  if not (args.has_key('private_data')):
    return logWith404("make_stash: request didn't pass private_data arg")

  stash_uuid = uuid.uuid4()
  session_id = request.COOKIES['session']
  req_session_id = args['sessionID']

  if req_session_id != session_id:
    return logWith404("make_stash: request session_id %s didn't match cookie\
        session_id %s" % (req_session_id, session_id))

  sessions = BelaySession.objects.filter(session_id=session_id)
  if len(sessions) == 0:
    return logWith404("make_stash: request session_id: %s didn't match any sessions"\
        % session_id)
  if len(sessions) != 1:
    return logWith404('make_stash: found duplicate BelaySessions', level='warn')

  session = sessions[0]
  stashed_content = bcap.dataPreProcess(args['private_data'])
  stash = Stash(session=session, stashed_content=stashed_content)
  stash.save()

  cap = bcap.grant('get-stash', stash)
  return bcap.bcapResponse(cap)

class GetStashHandler(bcap.CapHandler):
  def get(self, grantable):
    return HttpResponseNotAllowed(['POST'])
  def post(self, grantable, args):
    stash = grantable.stash
    req_session_id = args['sessionID']

    if stash.session.session_id != req_session_id:
      return logWith404("GetStashHandler: request session_id didn't match")

    return bcap.bcapResponse(bcap.dataPostProcess(stash.stashed_content))
