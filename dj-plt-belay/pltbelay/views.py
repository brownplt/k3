from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string
from pltbelay.models import BelaySession, PltCredentials, GoogleCredentials
from lib.py.bs import bs
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

logger = logging.getLogger('default')

GENERATE_STATION = "http://localhost:9001/belay/generate"
def unameExists(uname):
  q = PltCredentials.objects.filter(username=uname)
  logging.debug('checking')
  return len(q) == 1

HASH_ITERATIONS = 20
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.md5()
    m1.update(salted)
    salted = m1.hexdigest()

  logging.debug("Salted: %s" % salted)
  return salted

def get_station(request):
  if not 'session' in request.COOKIES:
    logger.debug('Failed to find session')
    return HttpResponse(status=500)
    
  sid = request.COOKIES['session']
  q = BelaySession.objects.filter(session_id=sid)
  if len(q) == 0:
    acct = None
  else:
    acct = q[0]

  return HttpResponse(acct.station_url)

def create_plt_account(request):
  if request.method != 'POST':
    return HttpResponse("only POST is implemented", status=500)

  keys = request.POST.keys()
  if not ('username' in keys and 'password' in keys):
    logger.error('create_plt_account: post data missing username or password')
    return HttpResponse(status=500)

  username = request.POST['username']
  rawpassword = request.POST['password']

  if len(username) > 20:
    return HttpResponse('Failed: Bad uname')

  if len(rawpassword) < 8:
    return HttpResponse('Failed: Bad password')

  salt = str(uuid.uuid4())
  hashed_password = get_hashed(rawpassword, salt)

  station_cap = bcap.Capability(GENERATE_STATION).invoke('GET')

  account = model.BelayAccount(station_url=station_cap.serialize())
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
  soup = bs.BeautifulSoup(f.read()) 
  uris = soup.findAll("uri")

  if len(uris) != 1:
    return HttpResponse("Error contacting Google OID endpoint", status=500)
  raw_uri = uris[0].contents[0]
  parsed = urlparse(raw_uri)

  param_obj = {
      'openid.ns' : 'http://specs.openid.net/auth/2.0',
      'openid.claimed_id' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.identity' : 'http://specs.openid.net/auth/2.0/identifier_select',
      'openid.return_to' : 'http://66.228.37.176:8000/glogin_landing/',
      'openid.realm' : 'http://66.228.37.176:8000',
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
    # TODO: call station.  for now, account has a dummy station_url
    dummy_url = str(uuid.uuid4())
    account = BelayAccount(station_url=dummy_url)
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

def belay_frame(request):
  rendered = render_to_string("belay-frame.html", {})
  return HttpResponse(rendered)

def check_uname(request):
  uname = request.POST['username']
  if unameExists(uname):
    return HttpResponse('Taken', status=200)
  else:
    return HttpResponse('Available', status=200)

def check_login(request):
  if not ('session' in request.COOKIES):
    return HttpResponse("false")
  session_id = request.COOKIES['session']
  sessions = BelaySession.objects.filter(session_id=session_id)
  if len(sessions) == 0:
    return HttpResponse("false")
  return HttpResponse("true")
