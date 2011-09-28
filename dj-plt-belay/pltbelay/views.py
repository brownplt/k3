from django.http import HttpResponse, HttpRequest
from pltbelay.models import BelaySession, PltCredentials
import logging
import uuid
import hashlib

import belaylibs.dj_belay as belay

import models as model

logger = logging.getLogger(__name__)

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

  # TODO: port station to django
  station_cap = belay.Capability(GENERATE_STATION).invoke('GET')

  account = model.BelayAccount(station_url=station_cap.serialize())
  account.save()
  credentials = PltCredentials(username=username, \
    salt=salt, \
    hashed_password=hashed_password, \
    account=account)
  credentials.save()

  session_id = str(uuid.uuid4())

  # TODO: port station to django
  #logger.debug("Session id: %s" % session_id)
  #session = BelaySession(session_id=session_id, account=account)
  #session.save()

  response = HttpResponse()
  cstr = 'session=%s; expires=Sun,31-May-2040 23:59:59 GMT; path=/;' % session_id
  response['Set-Cookie'] = cstr
  return response

# TODO : google login
def glogin(request):
  return HttpResponse("Google Login NYI", status=500)

def plt_login(request):
  return HttpResponse("Google Login NYI", status=500)

def check_uname(request):
  uname = request.POST['username']
  if unameExists(uname):
    return HttpResponse('Taken', status=200)
  else:
    return HttpResponse('Available', status=200)

def check_login(request):
  return HttpResponse("Check_login NYI", status=500)

