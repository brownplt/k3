import logging
import uuid
import hashlib
import os
import subprocess

from django.core.validators import validate_email
from django.http import HttpResponseNotFound, HttpResponseNotAllowed

import settings

from contwinue.models import *
from contwinue.email import send_and_log_email, notFoundResponse
import contwinue.email_strings as strings
import contwinue.files as files

import belaylibs.dj_belay as bcap
from belaylibs.models import Grant

from lib.py.common import logWith404, make_get_handler

logger = logging.getLogger('default')

index_handler = make_get_handler('login.html', {})

def conf_from_path(request):
  path = request.path_info
  slash = path.find('/', 1)
  if slash == -1: return (True, logWith404(logger, 'Badly formed path: %s' % path))

  shortname = path[1:slash]
  return (False, Conference.get_by_shortname(shortname))

def get_launch(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  key = args['key']
  account = get_one(Account.objects.filter(key=key))
  if key is None: return logWith404('Bad account: %s' % key)

  return bcap.bcapResponse(account.get_launchables())

def create_user(request):
  if request.method != 'POST':
    return HttpResponseNotAllowed(['POST'])
  (err, conf) = conf_from_path(request)
  if err: return conf

  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  key = args['key']
  account = get_one(Account.objects.filter(key=key))
  if key is None: return logWith404('Bad account: %s' % key)

  gcreds = get_one(GoogleCredentials.objects.filter(account=account))

  if get_one(User.objects.filter(email=gcreds.email)):
    return bcap.bcapResponse({'error': True, 'message': 'Account exists'})
  user = User(username=gcreds.email,
              email=gcreds.email,
              full_name=u'',
              conference=conf,
              account=account)
  user.save()
  user.roles.add(get_one(Role.objects.filter(name='user')))

  paper = Paper(contact=user,
                author=args['email'],
                title=u'',
                target=conf.default_target,
                conference=conf)
  paper.save()

  paper.authors.add(user)
  paper.save()

  launchcap = bcap.grant('launch-paper', {'user': user, 'paper': paper})
  launchbase = '%s/paper' % bcap.this_server_url_prefix()

  launchable = Launchable(account=account,
                          launchbase=launchbase,
                          launchcap=bcap.cap_for_hash(launchcap),
                          display='See my papers')
  launchable.save()

  return bcap.bcapResponse(account.get_launchables())

def continue_login(request):
  args = bcap.dataPostProcess(request.read())
  args.update(request.POST)

  logger.error('ARGS: %s', args)

  email = args['email']
  password = args['password']

  creds = ContinueCredentials.objects.filter(username=email)

  for c in creds:
    salt = c.salt
    hashed_password = get_hashed(password, salt)
    if c.hashed_password == hashed_password:
      account = c.account
      return bcap.bcapResponse({'launch': c.account.get_launchables()})

  return bcap.bcapResponse({
    'error': True,
    'message': 'No account found for that email and password'
  })

def get_basic(request):
  (err, conference) = conf_from_path(request)
  if err: return logWith404(logger, 'Conf not found: %s' % shortname)

  return bcap.bcapResponse(conference.get_title_and_contact())

paper = make_get_handler('writer.html', {})

# UserUpdateNameHandler

# Change a user's full_name.  Returns the name after updating it

# granted: |user:User|
# -> {'name' : uString}
# <- {'name' : uString}
class UserUpdateNameHandler(bcap.CapHandler):
  def post_arg_names(self): return ['name']
  def post(self, granted, args):
    user = granted.user
    user.full_name = args['name']
    user.save()
    return bcap.bcapResponse({'name': user.full_name})

class WriterBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic = granted.conference.get_writer_basic()
    return bcap.bcapResponse(basic)

class WriterPaperInfoHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted['paper'].paper
    caller = granted['writer'].user
    author_json = []
    for author in paper.authors.all():
      if caller == author: continue
      if caller == paper.contact and author != caller:
        remove = bcap.grant('paper-remove-author', {
          'user': author,
          'paper': paper
        })
      else: 
        remove = None
      author_json.append({
        'email': author.email,
        'name': author.full_name,
        'added': True,
        'remove': remove
      }) 
    unverified_author_json = []
    for author in paper.unverified_authors.all():
      if caller == paper.contact:
        remove = bcap.grant('paper-remove-author', {
          'unverified': author,
          'paper': paper
        })
      else:
        remove = None
      unverified_author_json.append({
        'email': author.email,
        'name': author.name,
        'added': False,
        'remove': remove
      }) 
    paper_json = paper.get_paper()
    paper_json['authors'] = author_json
    paper_json['unverifiedAuthors'] = unverified_author_json
    paper_json['thisAuthor'] = {
      'email': caller.email,
      'name': caller.full_name
    }
    return bcap.bcapResponse(paper_json)

class AuthorTextHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.conference.get_author_text())

class PaperDeadlineExtensionsHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.paper.get_deadline_extensions())

class PaperSetTitleHandler(bcap.CapHandler):
  def post_arg_names(self): return ['title']
  def post(self, granted, args):
    granted.paper.title = args['title']
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetAuthorHandler(bcap.CapHandler):
  def post_arg_names(self): return ['author']
  def post(self, granted, args):
    granted.paper.author = args['author']
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetPcPaperHandler(bcap.CapHandler):
  def post_arg_names(self): return ['pcpaper']
  def post(self, granted, args):
    if args['pcpaper'] == 'yes':
      granted.paper.pc_paper = True
    else:
      granted.paper.pc_paper = False
    granted.paper.save()
    granted.paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class PaperSetTargetsHandler(bcap.CapHandler):
  def post_arg_names(self): return ['targetID', 'othercats']  
  def post(self, granted, args):
    paper = granted.paper
    paper.update_target_by_id(args['targetID'])
    paper.update_othercats(args['othercats'])
    paper.save()
    paper.conference.update_last_change(paper)
    return bcap.bcapResponse(paper.get_paper())

class PaperSetTopicsHandler(bcap.CapHandler):
  def post_arg_names(self): return ['topics']
  def post(self, granted, args):
    paper = granted.paper
    paper.topic_set.clear()
    for t in args['topics']:
      for topic in Topic.get_by_conference_and_id(paper.conference, t):
        topic.papers.add(paper)
        topic.save()
    paper.save()
    paper.conference.update_last_change(granted.paper)
    return bcap.bcapResponse(granted.paper.get_paper())

class GetComponentFileHandler(bcap.CapHandler):
  def get(self, granted):
    comp = granted.component
    if comp.type.fmt == 'Text':
      return logWith404(logger, 'Couldn\'t get component of type text')
    fname = os.path.join(settings.SAVEDFILES_DIR, '%d-%d-component' %
      (comp.paper.id, comp.type.id))
    response = files.file_response(fname, comp.value)
    print(response.__class__)
    return response

class PaperUpdateComponentsHandler(bcap.CapHandler):
  def post_arg_names(self): return []
  def all_files(self): return True
  def post_files(self, granted, args, files):
    thetime = time.time()
    paper = granted.paper
    conf = paper.conference
    def check_deadlines_and_save(args, saver):
      ret = False
      for key, val in args.iteritems():
        ct = conf.component_type_by_abbr(key)
        if ct is None: continue
        deadline = ct.deadline
        de = DeadlineExtension.get_by_ct_and_paper(ct, paper)
        if not (de is None):
          deadline = de.until
        if (thetime > deadline+(ct.grace_hours*3600)):
          # Differs from contwinue.py:  All the files are in the files dict
          excomp = get_one(Component.objects.filter(type=ct, paper=paper))
          if (not excomp) or (excomp.value != val):
            ret = {'error': 'You cannot upload a component after its deadline.'}
          continue
        excomp = get_one(Component.objects.filter(type=ct, paper=paper))
        ret = saver(ct, excomp, val)
      if ret: return ret
      return False

    def save_text(ct, excomp, val):
      if ct.fmt == 'Text':
        if (excomp and val == excomp.value) or (not excomp and val ==''):
          return
        if excomp: excomp.delete() # TODO(joe): deleting the same as destroySelf()?
        newcomp = Component(
          conference=conf, type=ct, paper=paper,
          lastSubmitted=int(thetime), # use thetime again---all submitted simultaneously
          value=val, # TODO(joe): escaping?
          mimetype='text/plain'
        )
        newcomp.save()
      else:
        if val != '':
          raise Exception('Non-text component in args dictionary')

    def save_files(ct, excomp, f):
      val = f.read()
      if ct.fmt == 'PDF' and val[0:4] != '%PDF':
        return {'error': 'The file you uploaded was not a PDF document.'}
      if ct.size_limit != 0 and len(val) > ct.size_limit * 1024 * 1024:
        return {'error': 'The file you uploaded exceeds the size limit'}
      if excomp: excomp.delete()
      ofname = os.path.join(settings.SAVEDFILES_DIR, '%d-%d-component' %
        (paper.id, ct.id))
      outfile = open(ofname, 'w')
      outfile.write(val)
      outfile.close()
      mimetype = subprocess.Popen(['file', '-bi', ofname],stdout=subprocess.PIPE).communicate()[0][:-1]
      newcomp = Component(
        conference=paper.conference,
        type=ct,
        paper=paper,
        lastSubmitted=thetime,
        value=f.name,
        mimetype=mimetype
      )
      newcomp.save()

    text_response = check_deadlines_and_save(args, save_text)
    paper.conference.update_last_change(paper)
    if text_response: return bcap.bcapResponse(text_response)

    docs_response = check_deadlines_and_save(files, save_files)
    paper.conference.update_last_change(paper)
    if docs_response: return bcap.bcapResponse(docs_response)

    return bcap.bcapResponse(True)


class AssociateHandler(bcap.CapHandler):
  def post_arg_names(self): return ['key']
  def post(self, granted, args):
    user = granted.user
    account = get_one(Account.objects.filter(key=args['key']))
    if account is None:
      return logWith404(logger, 'Bad associate key for %s: %s' %
        (user.email, args['key']))

    cred = get_one(ContinueCredentials.objects.filter(account=account))
    cred.account = user.account
    cred.save()
    return bcap.bcapResponse({'success': True})


class AddGoogleAccountHandler(bcap.CapHandler):
  def post_arg_names(self): return ['key', 'new']
  def post(self, granted, args):
    user = granted.user

    newaccount = get_one(Account.objects.filter(key=args['key']))
    users = get_one(User.objects.filter(account=newaccount))
    if users is not None:
      return bcap.bcapResponse({
        'error': True,
        'message': 'That Google account is associated with a different Continue account.  You will have to manage them separately.'
      })
    cred = get_one(GoogleCredentials.objects.filter(account=newaccount))
    cred.account = user.account
    cred.save()

    return bcap.bcapResponse(user.account.get_credentials()['googleCreds'])
          


HASH_ITERATIONS = 20
# TODO: non-ASCII characters can break this
# need to sanitize raw password
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.sha1()
    m1.update(salted)
    salted = m1.hexdigest()
  return salted

class AddPasswordHandler(bcap.CapHandler):
  def post_arg_names(self): return ['password']
  def post(self, granted, args):
    password = args['password']
    user = granted.user

    salt = str(uuid.uuid4())
    credentials = ContinueCredentials(
      username=user.email,
      hashed_password=get_hashed(password, salt),
      salt=salt,
      account=user.account
    )
    credentials.save()

    return bcap.bcapResponse(user.account.get_credentials())

# AddAuthorHandler
# Adds an author to a paper, and sends email notification
# granted: {'paper':|paper:Paper|, 'user':|user:User|}
# -> {email: string, name: string}
# <- {email: string, name: string} U emailError
class AddAuthorHandler(bcap.CapHandler):
  def post_arg_names(self): return ['email', 'name']
  def post(self, granted, args):
    paper = granted['paper'].paper
    user = granted['user'].user
    conf = user.conference
    email = args['email']
    name = args['name']

    try:
      validate_email(email)
    except Exception as e:
      return notFoundResponse()

    existing_user = get_one(User.objects.filter(
      email=email,
      conference=conf
    ))

    if existing_user is None:
      existing_uu = get_one(UnverifiedUser.objects.filter(
        email=email,
        conference=conf
      ))
      if existing_uu is None:
        uu = UnverifiedUser(
          name=name,
          email=email,
          conference=conf,
          roletext=u'user'
        )
        uu.save()
      else:
        uu = existing_uu

      paper.unverified_authors.add(uu)
      paper.save()

      launch = bcap.grant('launch-attach-to-paper', {
        'newuser': True,
        'unverified': uu,
        'paper': paper
      })
      launchurl = '%s/paper#%s' %\
        (bcap.this_server_url_prefix(), bcap.cap_for_hash(launch))
      subject = strings.add_author_subject % {
        'confname': conf.name,
        'paper_title': paper.title
      }
      body = strings.add_author_body % {
        'authorname': name,
        'paper_title': paper.title,
        'confname': conf.name,
        'launchurl': launchurl
      }
      fromaddr = "%s <%s>" % (conf.name, conf.admin_contact.email)
      e_response = send_and_log_email(subject, body, email, fromaddr, logger)
      if e_response: return e_response

      remove = bcap.grant('paper-remove-author', {
        'unverified': uu,
        'paper': paper
      })
      return bcap.bcapResponse({
        'name': name,
        'email': email,
        'remove': remove
      })
    else:
      paper.authors.add(existing_user)
      paper.save()
      launch = bcap.grant('launch-paper', {
        'user': existing_user,
        'paper': paper
      })
      launchurl = '%s/paper#%s' %\
        (bcap.this_server_url_prefix(), bcap.cap_for_hash(launch))
      subject = strings.add_author_subject % {
        'confname': conf.name,
        'paper_title': paper.title
      }
      body = strings.add_author_body % {
        'authorname': existing_user.full_name,
        'paper_title': paper.title,
        'confname': conf.name,
        'launchurl': launchurl
      }
      fromaddr = "%s <%s>" % (conf.name, conf.admin_contact.email)
      e_response = send_and_log_email(subject, body, email, fromaddr, logger)
      if e_response: return e_response

      remove = bcap.grant('paper-remove-author', {
        'user': existing_user,
        'paper': paper
      })
      return bcap.bcapResponse({
        'name': existing_user.full_name,
        'email': email,
        'remove': remove
      })


# RemoveAuthorHandler

# Remove an author from a paper.  The author can be verified or unverified.

# Granted:  {'user':|user:User|, 'paper':|paper:Paper|}
#         U {'unverified':|unverified:Unverified|, 'paper':|paper:Paper|}
# -> {}
# <- {'success': True}
class RemoveAuthorHandler(bcap.CapHandler):
  def post_arg_names(self): return []
  def post(self, granted, args):
    paper = granted['paper'].paper
    if granted.has_key('user'):
      paper.authors.remove(granted['user'].user)
      return bcap.bcapResponse({'success': True})
    elif granted.has_key('unverified'):
      paper.unverified_authors.remove(granted['unverified'].unverifieduser)
      return bcap.bcapResponse({'success': True})
    return logWith404(logger, 'No user or unverified in RemoveAuthorHandler')

class AddPaperHandler(bcap.CapHandler):
  def post_arg_names(self): return ['title']
  def post(self, granted, args):
    user = granted.user
    conf = user.conference
    paper = Paper(
        contact=user,
        author=user.full_name,
        title=args['title'],
        target=conf.default_target,
        conference=conf
      )
    paper.save()

    paper.authors.add(user)
    paper.save()

    paper_json = {
      'getPaper': bcap.regrant('writer-paper-info', {
        'writer': user,
        'paper': paper
      }),
      'setTitle': bcap.regrant('paper-set-title', paper),
      'setAuthor': bcap.regrant('paper-set-author', paper),
      'setPcPaper': bcap.regrant('paper-set-pcpaper', paper),
      'setTarget': bcap.regrant('paper-set-target', paper),
      'setTopics': bcap.regrant('paper-set-topics', paper),
      'getDeadlineExtensions': bcap.regrant('paper-deadline-extensions', paper),
      'title': paper.title,
      'id': paper.id
    }
    launchcap = bcap.regrant('launch-paper', {'user': user, 'paper': paper})
    launchbase = '%s/paper' % bcap.this_server_url_prefix()
    return bcap.bcapResponse({
      'success': True,
      'launch': {
        'launchcap': bcap.cap_for_hash(launchcap),
        'launchbase': launchbase
      }
    })

# paper_launch_info : User, Paper, boolean -> launch-dict
# Gets the information the paper# page needs to get started, for this
# user and the given paper as the default to show
# |newuser| controls whether to show the 'welcome' dialog or not
def paper_launch_info(user, paper, newuser):

  account = get_one(Account.objects.filter(user=user))

  papers = user.get_papers()
  paper_jsons = []
  
  for p in papers:
    paper_json = {
      'paperContactName': p.contact.full_name,
      'paperContactEmail': p.contact.email,
      'getPaper': bcap.regrant('writer-paper-info', {
        'writer': user,
        'paper': p
      }),
      'setTitle': bcap.regrant('paper-set-title', p),
      'setAuthor': bcap.regrant('paper-set-author', p),
      'addAuthor': bcap.regrant('paper-add-author', {
        'user': user,
        'paper': paper
      }),
      'setPcPaper': bcap.regrant('paper-set-pcpaper', p),
      'setTarget': bcap.regrant('paper-set-target', p),
      'setTopics': bcap.regrant('paper-set-topics', p),
      'getDeadlineExtensions': bcap.regrant('paper-deadline-extensions', p),
      'updateComponents': bcap.regrant('paper-update-components', p),
      'title': p.title,
      'id': p.id
    }
    paper_jsons.append(paper_json)

  return bcap.bcapResponse({
    'newUser': newuser,
    'name': user.full_name,
    'email': user.email,
    'updateName': bcap.regrant('user-update-name', user),
    'accountkey': account.key,
    'addPassword': bcap.regrant('add-password', user),
    'addGoogleAccount': bcap.regrant('add-google-account', user),
    'credentials': user.get_credentials(),
    'papers': paper_jsons,
    'mainTitle': paper.title,
    'addPaper': bcap.regrant('add-paper', user),
    'getBasic': bcap.regrant('writer-basic', paper.conference),
    'getAuthorText': bcap.regrant('author-text', paper.conference),
  })

# make_user: UnverifiedUser -> (Account, User)
# Creates a user object and an account object from this unverified user
# Move any paper associations over
# Exceptions not handled:
#  - A user with this email already exists.  Will throw a DB exception.
def make_user(uu):
  key = str(uuid.uuid4())
  account = Account(
    key=key
  )
  account.save()

  user = User(
    full_name=uu.name,
    email=uu.email,
    conference=uu.conference,
    account=account
  )
  user.save()
  role = get_one(Role.objects.filter(name=uu.roletext))
  user.roles.add(role)

  for paper in uu.paper_set.all():
    paper.unverified_authors.remove(uu)
    user.papers.add(paper)

  return (account, user)

def make_user_with_paper_launch(uu, paper):
  (account, user) = make_user(uu)
  launch = bcap.grant('launch-paper', {
    'user': user,
    'paper': paper
  })
  launchable = Launchable(
    account = account,
    launchbase = '%s/paper' % bcap.this_server_url_prefix(),
    launchcap = bcap.cap_for_hash(launch),
    display = ''
  )
  launchable.save()
  return (account, user)

def new_paper(contact):
  paper = Paper(
    contact=contact,
    conference=contact.conference,
    title=u'',
    target=contact.conference.default_target
  )
  paper.save()
  paper.authors.add(contact)
  paper.save()

  return paper

# LaunchNewPaperHandler

# Creates a new paper for this unverified user (if the handler hasn't already),
# and then returns the launch info for that paper and user.

# If the unverified_user exists as a user (the email is taken), create a paper
# for that user if they have none, and then launch.

# granted:  {'create':True,  'unverified':|unverified_user:UnverifiedUser|}
#         U {'create':False, 'user':|user:User|, 'paper':|paper:Paper|}
# <- { <paper-launch-dict> }
class LaunchNewPaperHandler(bcap.CapHandler):
  def get(self, granted):
    if not granted['create']:
      return paper_launch_info(granted['user'].user, granted['paper'].paper, False)

    uu = granted['unverified'].unverifieduser
    existing_user = get_one(User.objects.filter(email=uu.email))
    if not (existing_user is None):
      papers = existing_user.get_papers()
      if len(papers) == 0:
        paper = new_paper(existing_user)
      else:
        paper = papers[0]
      self.updateGrant({
        'create': False,
        'user': existing_user,
        'paper': paper
      })
      return paper_launch_info(existing_user, paper, True)

    (account, user) = make_user(uu)

    paper = new_paper(user)
    launchable = Launchable(
      account=user.account,
      launchbase='%s/paper' % bcap.this_server_url_prefix(),
      launchcap=bcap.cap_for_hash(bcap.grant('launch-paper', {
        'user': user,
        'paper': paper
      })),
      display=''
    )
    launchable.save()
    self.updateGrant({
      'create': False,
      'user': user,
      'paper': paper
    })
    return paper_launch_info(user, paper, True)

# LaunchAttachToPaperHandler

# Changes the granted UnverifiedUser to a User, and after acts like a 
# LaunchPaperHandler on that User and Paper.  If the user already exists
# (via overlapping email), immedately turn into a LaunchPaperHandler

# granted:  {'newuser': True, 'unverified':|unverifieduser:UnverifiedUser|,
#            'paper':|paper:Paper|}
#         U {'newuser': False, 'user':|user:User|, 'paper':|paper:Paper|}
class LaunchAttachToPaperHandler(bcap.CapHandler):
  def get(self, granted):
    if granted['newuser'] == False:
      return paper_launch_info(granted['user'].user, granted['paper'].paper, False)

    uu = granted['unverified'].unverifieduser
    paper = granted['paper'].paper

    existing_user = get_one(User.objects.filter(email=uu.email))
    if not (existing_user is None):
      if not (paper in existing_user.papers.all()):
        existing_user.papers.add(paper)
        paper.unverified_authors.remove(uu)
        paper.save()
        existing_user.save()
      self.updateGrant({
        'newuser': False,
        'user': existing_user,
        'paper': paper
      })
      return paper_launch_info(existing_user, paper, False)

    (account, user) = make_user_with_paper_launch(uu, paper)
    return paper_launch_info(user, granted['paper'].paper, True)

# LaunchPaperHandler

# Launches the paper page for a user and a paper

# granted: {'user':|user:User|, 'paper':|paper:Paper|}
# <- { <launch-paper-dict> }
class LaunchPaperHandler(bcap.CapHandler):
  def get(self, granted):
    return paper_launch_info(granted['user'].user, granted['paper'].paper, False)

class GetAdminHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_admin())

class GetAllHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_all())

class AddTopicHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name']

  def post(self, granted, args):
    conference = granted.conference
    name = args['name']

    if conference.has_topic_named(name):
      t = conference.get_topic_by_name(name)
    else:
      try:
        t = Topic(name=args['name'], conference=granted.conference)
        t.save()
      except Exception as e:
        return logWith404(logger, 'AddTopicHandler: %s' % e, level='error')

    return bcap.bcapResponse(t.to_json())

class DeleteTopicHandler(bcap.CapHandler):
  def delete(self, granted):
    topic = granted.topic
    try:
      topic.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteTopicHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddDecisionValueHandler(bcap.CapHandler):
  def post_arg_name(self):
    return ['abbr', 'description', 'targetable']

  def post(self, granted, args):
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']
    targetable = args['targetable']

    if conference.has_decision_value(targetable, abbr, description):
      ndv = conference.get_decision_value(targetable, abbr, description)
    else:
      try:
        ndv = DecisionValue(targetable=targetable, abbr=abbr, \
          description=description, conference=conference)
        ndv.save()
      except Exception as e:
        return logWith404(logger, 'AddDecisionValueHandler: %s' % e, level='error')

    return bcap.bcapResponse(ndv.to_json())

class DeleteDecisionValueHandler(bcap.CapHandler):
  def delete(self, granted):
    dv = granted.decisionvalue
    try:
      dv.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteDecisionHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddReviewComponentTypeHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['description', 'pcOnly']

  def post(self, granted, args): 
    conference = granted.conference
    description = args['description']
    pc_only = args['pcOnly']

    if conference.has_rc_type(description, pc_only):
      rct = conference.get_rc_type(description, pc_only)
    else:
      try:
        rct = ReviewComponentType(description=description, pc_only=pc_only,\
          conference=conference)
        rct.save()
      except Exception as e:
        return logWith404(logger, 'AddReviewComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(rct.to_json())

class AddComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args): 
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']

    if conference.has_component_type(abbr):
      ct = conference.component_type_by_abbr(abbr)
    else:
      try:
        ct = ComponentType(abbr=abbr, description=description,\
          fmt=args['format'], size_limit=args['sizelimit'],\
          deadline=args['deadline'], grace_hours=args['gracehours'],\
          mandatory=args['mandatory'], conference=conference)
        ct.save()
      except Exception as e:
        return logWith404(logger, 'AddComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(ct.to_json())

class DeleteComponentTypeHandler(bcap.CapHandler):
  def delete(self, granted):
    ct = granted.componenttype
    try:
      ct.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteComponentType: %' % e,\
        level='error')
    return bcap.bcapNullResponse()

class ChangeComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args):
    ct = granted.componenttype
    ct.fmt = args['format']
    ct.abbr = args['abbr']
    ct.description = args['description']
    ct.size_limit = args['sizelimit']
    ct.deadline = args['deadline']
    ct.grace_hours = args['gracehours']
    ct.mandatory = args['mandatory']

    try:
      ct.save()
    except Exception as e:
      return logWith404(logger, 'ChangeComponentType: %' % e,\
        level='error')
    
    return bcap.bcapResponse(ct.to_json())

class ChangeUserEmailHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def post(self, granted, args):
    user = granted.user
    try:
      user.email = args['email']
      user.save()
    except Exception as e:
      return logWith404(logger, 'ChangeUserEmailHandler: %s' % e,\
        level='error')

    return bcap.bcapResponse('true')

# In contwinue.py, this is handle_getIDsByDecision
# Here, instead of passing the decision value ID, the decision value is part
# of the grant
class GetPapersOfDVHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted['conference'].conference
    decision_value = granted['decision_value'].decisionvalue

    return bcap.bcapResponse(conference.papers_of_dv(decision_value))

class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'user-update-name': UserUpdateNameHandler,

      'add-password': AddPasswordHandler,
      'add-google-account': AddGoogleAccountHandler,
      'add-paper': AddPaperHandler,
      'writer-basic': WriterBasicHandler,
      'writer-paper-info': WriterPaperInfoHandler,
      'author-text': AuthorTextHandler,
      'paper-deadline-extensions': PaperDeadlineExtensionsHandler,
      'paper-set-title': PaperSetTitleHandler,
      'paper-add-author': AddAuthorHandler,
      'paper-remove-author': RemoveAuthorHandler,
      'paper-set-author': PaperSetAuthorHandler,
      'paper-set-pcpaper': PaperSetPcPaperHandler,
      'paper-set-target': PaperSetTargetsHandler,
      'paper-set-topics': PaperSetTopicsHandler,
      'paper-update-components': PaperUpdateComponentsHandler,
      'get-component-file': GetComponentFileHandler,
      'launch-paper': LaunchPaperHandler,
      'launch-new-paper': LaunchNewPaperHandler,
      'launch-attach-to-paper': LaunchAttachToPaperHandler,
      'get-papers-of-dv': GetPapersOfDVHandler,
      # End LaunchPaper handlers

      'get-admin': GetAdminHandler,
      'get-all': GetAllHandler,
      'add-topic': AddTopicHandler,
      'delete-topic': DeleteTopicHandler,
      'add-decision-value': AddDecisionValueHandler,
      'delete-decision-value': DeleteDecisionValueHandler,
      'add-review-component-type': AddReviewComponentTypeHandler, 
      'add-component-type': AddComponentTypeHandler,
      'delete-component-type': DeleteComponentTypeHandler,
      'change-component-type': ChangeComponentTypeHandler,
      'change-user-email': ChangeUserEmailHandler,
      # End LaunchAdmin handlers

      # End LaunchContinue handlers

      # End LaunchMeeting handlers

      # End LaunchPaperView handlers
    })
    return None
