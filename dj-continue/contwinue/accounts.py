from django.core.validators import validate_email
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
 ContinueCredentials, Account, Conference
from contwinue.email import send_and_log_email

logger = logging.getLogger('default')

def conf_from_path(request):
  path = request.path_info
  slash = path.find('/', 1)
  if slash == -1: return (True, logWith404(logger, 'Badly formed path: %s' % path))

  shortname = path[1:slash]
  return (False, Conference.get_by_shortname(shortname))

class VerifyHandler(bcap.CapHandler):
  def post_arg_names(self): return []
  def post(self, grantable, args):
    pending = grantable.pending_account

    key = str(uuid.uuid4())
    account = Account(email=pending.email,
                      key=key)

    return bcap.bcapResponse({
      'email': email,
      'newaccount': True,
      'key': account_key
    })
    

def request_account(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  email = args['email']

  pending = PendingAccount(email=email)

  verify = bcap.grant('verify-pending', pending)

  message=u"""
You've made a request to submit a paper for %(confname)s.  This link will take
you to a page where you can verify your email and get started:

%(base)s/verify#%(key)s

If you run into any problems, simply reply to this email.

Thanks!
%(confname)s
"""

  filled_message = message % {
    'confname': conf.name,
    'base': bcap.this_server_url_prefix(),
    'key': verify.serialize()
  }

  subject = 'Create an Account for %s' % conf.name
  fromaddr = conf.admin_contact.email
  
  resp = send_and_log_email(subject, filled_message, email, fromaddr, logger)

  if resp: return resp
  return bcap.bcapResponse({'success': True})


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
    logger.error('Creating an account: %s' % email)
    account_key = str(uuid.uuid4())
    account = Account(email=email, key=account_key)
    account.save()
    newaccount = 'true'

    gc = GoogleCredentials(account=account, identity=identity)
    gc.save()
  else:
    account = q[0].account
    account_key = account.key
    newaccount = 'false'

  response = render_to_response('glogin.html', {
    'email': email,
    'newaccount': newaccount,
#    'launchables': account.get_launchables()),
    'key': account_key
  })

  return response


