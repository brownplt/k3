from django.shortcuts import redirect, render_to_response
from xml.dom import minidom
import logging
import urllib2
import urllib
from urlparse import urlparse
import uuid
import settings

from lib.py.common import logWith404

import belaylibs.dj_belay as bcap

from contwinue.models import PendingLogin, PendingAccount, GoogleCredentials,\
 ContinueCredentials, Account 

logger = logging.getLogger('default')

def glogin(request):
  if(request.method != 'GET'):
    logwith404(logger, "pltbelay: Tried to glogin with method: " % request.method)

  clientkey = str(request.GET['clientkey'])
  # NOTE(matt): I tried to use urllib.urlencode, but it translates slashes
  # into escape sequences
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
    if len(pl) == 1:
      ret = pl[0].clientkey
      pl.delete()
      return ret
    else:
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
    account_key = str(uuid.uuid4())
    account = Account(email=email, key=account_key)
    account.save()
    newaccount = True

    gc = GoogleCredentials(account=account, identity=identity)
    gc.save()
  else:
    account = q[0].account
    account_key = account.key
    newaccount = False

  response = render_to_response('glogin.html', {
    'email': email,
    'newaccount': newaccount,
#    'launchables': account.get_launchables()),
    'key': account_key
  })

  return response


