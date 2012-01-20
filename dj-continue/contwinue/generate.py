from contwinue.models import *
from django.http import HttpResponse
from lib.py.generate_tools import rand_str, rand_email, rand_bool
import logging
import sha
import random

logger = logging.getLogger('default')

def check_size(cls, num):
  return len(cls.objects.all()) == num

def simple_generate():
  conferences = Conference.objects.all()
  if len(conferences) == 0:
    c = Conference.make_new('Sample Conference', 'SC', 'admin', 'admin',
      'Joe Gibbs Politz', 'joe@cs.brown.edu', False)
  else:
    c = conferences[0]

  topics = ['Compilers', 'Type Systems', 'Contracts', 'Macros']
  if not check_size(Topic, len(topics)):
    for topic in topics:
      t = Topic(name=topic, conference=c)
      t.save()
  

def generate(numusers=10):
  """
  Generates sample data.
  Creates an admin/reviewer user (username: admin, pw: admin) and several 
  writer users (writer/writer, writer2/writer2, ..., writer10/writer10)
  """
  conferences = Conference.objects.all()
  if len(conferences) == 0:
    c = Conference.make_new('Sample Conference', 'SC', 'admin', 'admin',
      'Joe Admin', 'joe@fake.com', False)
  else:
    c = conferences[0]

  writer_roles = Role.objects.filter(name='writer')
  if len(writer_roles) == 0:
    writer_role = Role(name='writer', conference=c)
    writer_role.save()
  else:
    writer_role = writer_roles[0]


  writer_bios = ComponentType.objects.filter(abbr='B')
  if len(writer_bios) == 0:
    writer_bio = ComponentType(abbr='B', description='Writer Bio', fmt='Any',
      size_limit=20000, deadline=int(time.time())+(86400*15), mandatory=False,
      grace_hours=48, conference=c)
    writer_bio.save()

  extended_abstracts = ComponentType.objects.filter(abbr='C')
  if len(extended_abstracts) == 0:
    extended_abstract = ComponentType(abbr='C', description='Extended Abstract',
      fmt='Text', size_limit=1000, deadline=int(time.time())+1, mandatory=False,
      grace_hours=96, conference=c)
    extended_abstract.save()

  writer_users = User.objects.filter(roles=writer_role)
  if len(writer_users) != numusers:
    account = Account(key=str(uuid.uuid4()))
    account.save()
    writer_user = User(username='writer', full_name='Joe Writer',
      email='joe@writer.com',
      conference=c,
      account=account)
    # 2 saves because you can't add ManyToMany relationships until the instance
    # is saved
    writer_user.save()
    writer_user.roles.add(writer_role)
    writer_user.save()
    
    for n in range(2, numusers+1):
      account = Account(key=str(uuid.uuid4()))
      account.save()
      nstr = str(n)
      writer_user = User(username='writer%s' % nstr, 
        full_name='Joe Writer%s' % nstr, email='joe@writer%s.com' % nstr, 
        conference=c,
        account=account)
      writer_user.save()
      writer_user.roles.add(writer_role)
      writer_user.save()

  if not check_size(UnverifiedUser, 10):
    for _ in range(10):
      uu = UnverifiedUser(name=rand_str(10), email=rand_email(),
        roletext=rand_str(10), conference=c)
      uu.save()

  revrole = Role.objects.filter(name='reviewer')[0]
  reviewers = revrole.user_set.all()
  if not len(reviewers) >= 10:
    for n in range(10):
      account = Account(key=str(uuid.uuid4()))
      account.save()
      rev_user = User(username='reviewer%s' % n, 
        full_name='Joe Reviewer%s' % n, email='joe@reviewer%s.com' % n, 
        conference=c,
        account=account)
      rev_user.save()
      rev_user.roles.add(revrole)

  if not check_size(Topic, 10):
    topics = ['Programming Languages', 'Distributed Systems', 'Web Security', 
      'Computer Vision', 'Machine Learning', 'Computational Biology', 
      'Artificial Intelligence', 'Cryptography', 'Algorithms', 'Nanocomputing']
    for n in range(10):
      t = Topic(name=topics[n], conference=c)
      t.save()

  if not check_size(Paper, numusers):
    titles = [
      'A synchronized real-time cache related to a virtual secure technology',
      'An interactive secure compiler related to a synchronized binary interface',
      'An active functional solution embedded in an integrated functional agent',
      'A virtual functional compiler related to a collaborative programmable database',
      'An active digital work cluster related to an active real-time display',
      'An interactive logical language for a balanced functional network',
      'An integrated multimedia preprocessor derived from a scalable object-oriented agent',
      'An optimized multimedia language derived from a high-level watermarking network',
      'A dynamic binary preprocessor derived from a parameterized functional technology',
      'A dynamic binary preprocessor derived from a parameterized functional technology'
    ]
    def odd_true(num):
      if num % 2 == 0: return False
      else: return True

    targets = DecisionValue.objects.filter(targetable=True)
    for n in range(numusers):
      if n == 0:
        username = 'writer'
      else:
        username = 'writer%s' % str(n+1)
      contacts = User.objects.filter(username=username)
      contact = contacts[0]
      target = targets[n % len(targets)]
      p = Paper(contact=contact, author=contact.full_name, target=target,
        other_cats=(not (odd_true(n))), pc_paper=odd_true(n), hidden=False,
        conference=c, title=titles[n % len(titles)], decision=c.default_decision)
      p.save()
      p.authors.add(contact)
      p.save()
      component = Component(type=extended_abstract, paper=p, lastSubmitted=987214,
        value="This is actually pretty short", mimetype='text/plain', conference=c)
      component.save()

      abstract = get_one(ComponentType.objects.filter(abbr='A'))
      abs_comp = Component(type=abstract, paper=p, lastSubmitted=int(time.time()),
        value="Paper %s abstract" % p.id, mimetype='text/plain', conference=c)
      abs_comp.save()
  
      t = Topic.objects.all()[random.randint(0, 9)]
      t.papers.add(p)
      t.save()

  if not check_size(ReviewComponentType, 2):
    pc_comments = ReviewComponentType(
      conference=c,
      description='Comments for the PC (not sent to authors)',
      pc_only=True)
    pc_comments.save()
    author_comments = ReviewComponentType(
      conference=c,
      description='Comments for the Author',
      pc_only=False)
    author_comments.save()

  if not check_size(DecisionValue, 3):
    undecided = DecisionValue(conference=c, abbr='U', targetable=False, 
      description='Undecided')
    undecided.save()
    rejected = DecisionValue(conference=c, abbr='R', targetable=False, 
      description='Rejected')
    rejected.save()
    accepted = DecisionValue(conference=c, abbr='A', targetable=True, 
      description='Accepted')
    accepted.save()

  if not check_size(BidValue, 6):
    bidval_q = BidValue(conference=c, abbr='Q', 
      description='I would love to review this paper')
    bidval_q.save()
    bidval_r = BidValue(conference=c, abbr='R',
      description='I can review this paper if needed')
    bidval_r.save()
    bidval_s = BidValue(conference=c, abbr='S',
      description='No Preference')
    bidval_s.save()
    bidval_t = BidValue(conference=c, abbr='T',
      description="I don't want to review this paper")
    bidval_t.save()
    no_bid = BidValue(conference=c, abbr='U',
      description='I have not yet bid on this paper')
    no_bid.save()
    conf_bid = BidValue(conference=c, abbr='V',
      description='I am conflicted with this paper')
    conf_bid.save()

  """
  TODO(matt): bad random things, maybe fix later
  if len(Component.objects.all()) != 10:
    for _ in range(10):
      comp = Component(type=ComponentType.objects.all()[random.randint(0, 2)],
        paper=Paper.objects.all()[random.randint(0, 9)],
        last_submitted=random.randint(0, 100), value=rand_str(20),
        mimetype=rand_str(5), conference=c)
      comp.save()

  if len(DeadlineExtension.objects.all()) != 5:
    for _ in range(5):
      ext = DeadlineExtension(
        type=ComponentType.objects.all()[random.randint(0, 2)],
        paper=Paper.objects.all()[random.randint(0, 9)],
        until=int(time.time())+(86400*15))
      ext.save()
  """

  return HttpResponse('OK')

