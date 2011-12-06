import logging
import uuid
import hashlib
import os
import subprocess

from django.http import HttpResponseNotFound, HttpResponseNotAllowed

import settings

from contwinue.models import *

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
  
  if get_one(User.objects.filter(email=account.email)):
    return bcap.bcapResponse({'error': True, 'message': 'Account exists'})
  user = User(username=account.email,
              email=account.email,
              full_name=account.email,
              conference=conf)
  user.save()
  user.roles.add(get_one(Role.objects.filter(name='user')))
  user.accounts.add(account)
  user.save()

  paper = Paper(contact=user,
                author=args['email'],
                title=u'',
                target=conf.default_target,
                conference=conf)
  paper.save()

  launchcap = bcap.grant('launch-paper', {'writer': user, 'paper': paper})
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

class WriterBasicHandler(bcap.CapHandler):
  def get(self, granted):
    basic = granted.conference.get_writer_basic()
    return bcap.bcapResponse(basic)

class WriterPaperInfoHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted['paper'].paper
    return bcap.bcapResponse(paper.get_paper())

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

    user.accounts.add(account)
    user.save()
    return bcap.bcapResponse({'success': True})


class AddGoogleAccountHandler(bcap.CapHandler):
  def post_arg_names(self): return ['key', 'new']
  def post(self, granted, args):
    user = granted.user

    existing_accounts = user.accounts.all()

    newaccount = get_one(Account.objects.filter(key=args['key']))
    user.accounts.add(newaccount)
    user.save()

    if args['new']:
      for l in Launchable.objects.filter(account=newaccount):
        l.delete()

    for a in existing_accounts:
      for l in Launchable.objects.filter(account=a):
        l2 = Launchable(
          account=newaccount,
          launchcap=l.launchcap,
          launchbase=l.launchbase,
          display=l.display
        )
        l2.save()

    return bcap.bcapResponse(newaccount.get_credentials()['googleCreds'])
          


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
    account = granted.account

    salt = str(uuid.uuid4())
    credentials = ContinueCredentials(
      username=account.email,
      hashed_password=get_hashed(password, salt),
      salt=salt,
      account=account
    )
    credentials.save()

    return bcap.bcapResponse(account.get_credentials())

class AddPaperHandler(bcap.CapHandler):
  def post_arg_names(self): return []
  def post(self, granted, args):
    user = granted.user
    conf = user.conference
    paper = Paper(
        contact=user,
        author=user.full_name,
        title=u'',
        target=conf.default_target,
        conference=conf
      )
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
    launchcap = bcap.regrant('launch-paper', {'writer': user, 'paper': paper})
    launchbase = '%s/paper' % bcap.this_server_url_prefix()
    return bcap.bcapResponse({
      'success': True,
      'launch': {
        'launchcap': bcap.cap_for_hash(launchcap),
        'launchbase': launchbase
      }
    })

class LaunchPaperHandler(bcap.CapHandler):
  def get(self, granted):
    if 'unverified' in granted:
      uu = granted['unverified'].unverifieduser
      conf = uu.conference
      user = get_one(User.objects.filter(email=uu.email))
      logger.error('Trying to create paper')
      if user is None:
        user = User(
          email=uu.email,
          full_name=uu.name,
          conference=conf,
          username=uu.email
        )
        user.save()
        user.roles.add(get_one(Role.objects.filter(name='user')))

      logger.error('Trying to create paper')
      paper = Paper(
        contact=user,
        author=user.full_name,
        title=u'',
        target=conf.default_target,
        conference=conf
      )
      paper.save()

      key = str(uuid.uuid4())
      account = Account(key=key, email=user.email)
      account.save()

      user.accounts.add(account)
      user.save()

      current = self.getCurrentCap()
      launch = Launchable(
        launchbase=bcap.this_server_url_prefix() + '/paper',
        launchcap=bcap.cap_for_hash(current),
        display=u'',
        account=account
      )
      launch.save()

      logger.error('Trying to update grant')
      granted = {'writer': user, 'paper': paper}
      self.updateGrant(granted)
      newuser = True
    else:
      user = granted['writer'].user
      paper = granted['paper'].paper
      account = user.accounts.all()[0]
      key = account.key
      newuser = False

    papers = user.get_papers()
    paper_jsons = []
    
    for p in papers:
      paper_json = {
        'getPaper': bcap.regrant('writer-paper-info', {
          'writer': user,
          'paper': p
        }),
        'setTitle': bcap.regrant('paper-set-title', p),
        'setAuthor': bcap.regrant('paper-set-author', p),
        'setPcPaper': bcap.regrant('paper-set-pcpaper', p),
        'setTarget': bcap.regrant('paper-set-target', p),
        'setTopics': bcap.regrant('paper-set-topics', p),
        'getDeadlineExtensions': bcap.regrant('paper-deadline-extensions', p),
        'updateComponents': bcap.regrant('paper-update-components', p),
        'title': p.title,
        'id': p.id
      }
      paper_jsons.append(paper_json)

    logger.error('Trying to respond')
    #TODO(joe): Add an option to attach an account to the paper
    return bcap.bcapResponse({
      'newUser': newuser,
      'email': user.email,
      'accountkey': key,
      'addPassword': bcap.regrant('add-password', account),
      'addGoogleAccount': bcap.regrant('add-google-account', user),
      'credentials': user.get_credentials(),
      'papers': paper_jsons,
      'mainTitle': paper.title,
      'addPaper': bcap.regrant('add-paper', user),
      'getBasic': bcap.regrant('writer-basic', paper.conference),
      'getAuthorText': bcap.regrant('author-text', paper.conference),
    })


class ContinueInit():
  def process_request(self, request):
    bcap.set_handlers(bcap.default_prefix, {
      'add-password': AddPasswordHandler,
      'add-google-account': AddGoogleAccountHandler,
      'add-paper': AddPaperHandler,
      'writer-basic': WriterBasicHandler,
      'writer-paper-info': WriterPaperInfoHandler,
      'author-text': AuthorTextHandler,
      'paper-deadline-extensions': PaperDeadlineExtensionsHandler,
      'paper-set-title': PaperSetTitleHandler,
      'paper-set-author': PaperSetAuthorHandler,
      'paper-set-pcpaper': PaperSetPcPaperHandler,
      'paper-set-target': PaperSetTargetsHandler,
      'paper-set-topics': PaperSetTopicsHandler,
      'paper-update-components': PaperUpdateComponentsHandler,
      'launch-paper': LaunchPaperHandler,
      'get-papers-of-dv': GetPapersOfDVHandler,
      # End LaunchPaper handlers

      
      # End LaunchAdmin handlers
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
      # End LaunchContinue handlers

      # End LaunchMeeting handlers

      # End LaunchPaperView handlers
    })
    return None

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
