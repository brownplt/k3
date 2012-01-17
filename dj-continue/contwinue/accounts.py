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
 ContinueCredentials, Account, Conference, UnverifiedUser, User, get_one, Paper
from contwinue.email import send_and_log_email
import contwinue.email_strings as strings

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
    account.save()
    pending.delete()

    return bcap.bcapResponse({
      'email': email,
      'newaccount': True,
      'key': key
    })
  def get(self, grantable):
    return bcap.bcapResponse({ 'email': grantable.pending.email })


def request_account(request):
  def remind(user, conf):
    launch = bcap.grant('launch-paper', {
      'user': user,
      'paper': get_one(Paper.objects.filter(contact=user))
    })

    filled_message = strings.remind_account_str % {
      'confname': conf.name,
      'base': bcap.this_server_url_prefix(),
      'key': bcap.cap_for_hash(launch)
    }

    subject = strings.remind_account_subject % conf.name
    fromaddr = "%s <%s>" % (conf.name, conf.admin_contact.email)
    
    resp = send_and_log_email(subject, filled_message, email, fromaddr, logger)

    if resp: return resp
    return bcap.bcapResponse({'success': True})



  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  email = args['email']

  maybe_user = get_one(User.objects.filter(email=email,conference=conf))

  if maybe_user:
    return remind(maybe_user, conf)

  user = UnverifiedUser(
    name=u'',
    email=email,
    roletext=u'writer',
    conference=conf
  )
  user.save()

  launch = bcap.grant('launch-new-paper', {'create': True, 'unverified': user})

  filled_message = strings.request_account_str % {
    'confname': conf.name,
    'base': bcap.this_server_url_prefix(),
    'key': bcap.cap_for_hash(launch)
  }

  subject = strings.request_account_subject % conf.name
  fromaddr = "%s <%s>" % (conf.name, conf.admin_contact.email)
  
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
    account = Account(key=account_key)
    account.save()
    newaccount = 'true'

    gc = GoogleCredentials(account=account, identity=identity, email=email)
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

# new_reviewer : Conference, String, String -> UnverifiedUser
def new_reviewer(conf, name, email):
  uu = UnverifiedUser(
    conference=conf,
    name=name,
    email=email,
    roletext='reviewer'
  )
  uu.save()
  return uu

# send_new_reviewer_email : UnverifiedUser -> EmailResponse
# Sends an account creation email to the given UnverifiedUser
# The UnverifiedUser must have roletext='reviewer', or this is
# an error.  Thows Exceptions if emails are invalid or cannot
# be sent
def send_new_reviewer_email(unverified_user):
  if unverified_user.roletext != 'reviewer':
    raise Exception('Tried to send reviewer email to %s' % unverified_user.roletext)

  launch_cap = bcap.grant('launch-reviewer', {
    'newuser': True,
    'unverified': unverified_user
  })

  fromaddr = "%s <%s>" % \
    (unverified_user.conference.name,
     unverified_user.conference.admin_contact.email)

  return send_and_log_email(
    subject=strings.new_reviewer_subject % {
      'confname': unverified_user.conference.name
    },
    msg=strings.new_reviewer_body % {
      'confname': unverified_user.conference.name,
      'name': unverified_user.name,
      'base': bcap.this_server_url_prefix(),
      'key': bcap.cap_for_hash(launch_cap)
    },
    address=unverified_user.email,
    fromaddr=fromaddr,
    logger=logger
  )
