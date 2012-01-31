from contwinue.models import *
from django.http import HttpResponse
from lib.py.generate_tools import rand_str, rand_email, rand_bool
import logging
import sha
import random

from contwinue.submitter import PaperUpdateComponentsHandler

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
      'Joe Admin', 'joe@cs.brown.edu', False)
  else:
    c = conferences[0]

  writer_roles = Role.objects.filter(name='writer')
  if len(writer_roles) == 0:
    writer_role = Role(name='writer', conference=c)
    writer_role.save()
  else:
    writer_role = writer_roles[0]

  protected_type = ComponentType.objects.filter(abbr='V')
  if len(protected_type) == 0:
    protected_type = ComponentType(
      conference=c,
      abbr='V',
      description='Previous Review Updates',
      fmt='PDF',
      deadline=int(time.time())+(86400*30),
      mandatory=False,
      grace_hours=0,
      size_limit=0,
      protected=True
    )
    protected_type.save()


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

      abstract = get_one(ComponentType.objects.filter(abbr='A'))
      abs_comp = Component(type=abstract, paper=p, lastSubmitted=int(time.time()),
        value="Paper %s abstract" % p.id, mimetype='text/plain', conference=c)
      abs_comp.save()

      pcomp = get_one(ComponentType.objects.filter(abbr='P'))
      f1 = open('testdata/testpdf.pdf', 'r')
      f2 = open('testdata/response.pdf', 'r')
      filesDict = {
        'P': f1, 'V': f2
      }
      handler = PaperUpdateComponentsHandler()
      response = handler.post_files(p, {}, filesDict)
  
      t = Topic.objects.all()[random.randint(0, 9)]
      t.papers.add(p)
      t.save()

      p_comp = Component(type=protected_type, paper=p,
        lastSubmitted=int(time.time()), value='testdata/response.pdf',
        mimetype='text/plain', conference=c)
      p_comp.save()

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

  revrole = Role.objects.filter(name='reviewer')[0]
  reviewers = revrole.user_set.all()
  papers = Paper.objects.all()
  ratings = RatingValue.objects.all()
  experts = ExpertiseValue.objects.all()
  types = ReviewComponentType.objects.all()
  bidvalues = BidValue.objects.all()
  if not len(reviewers) >= 20:
    for n in range(20):
      account = Account(key=str(uuid.uuid4()))
      account.save()
      rev_user = User(username='reviewer%s' % n, 
        full_name='Joe Reviewer%s' % n, email='joe@reviewer%s.com' % n, 
        conference=c,
        account=account)
      rev_user.save()
      rev_user.roles.add(revrole)
      for p in random.sample(papers, int(len(papers) / 5)):
        b = Bid(
          paper=p, bidder=rev_user, conference=c,
          value=random.choice(bidvalues)
        )
        b.save()
      # Each reviewer reviews 1/5 papers
      for p in random.sample(papers, int(len(papers) / 5)):
        rev = Review(
          paper=p, conference=c, reviewer=rev_user,
          published=random.choice([True, False]),
          submitted=random.choice([True, False]),
          overall=random.choice(ratings),
          expertise=random.choice(experts),
          subreviewers="",
          last_saved=0,
        )
        rev.save()
        pc_comp = ReviewComponent(
          type=random.choice(types),
          review=rev,
          value=random.choice(ipsums),
          conference=c
        )
        pc_comp.save()


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

ipsums = ["""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean tempus aliquet auctor. Donec nisi nulla, ullamcorper ornare blandit at, sagittis sed neque. Cras pellentesque eros ac dolor dictum malesuada. Nunc dignissim aliquam leo, quis mattis nisi tincidunt accumsan. Mauris eget egestas turpis. Pellentesque accumsan massa porta purus suscipit vestibulum. Etiam turpis ligula, bibendum a porttitor at, ornare id nisi. Nulla dui risus, dictum eu euismod sed, pretium vel orci. Ut vulputate aliquam elit, et aliquam turpis luctus id. Mauris tempus auctor nulla. Integer tempor blandit libero, sit amet ornare sapien molestie a. Morbi posuere velit at tellus ultricies mattis. Sed feugiat cursus molestie. Donec fringilla, ligula vel congue egestas, sem lacus ultricies massa, ac venenatis felis mauris quis tortor. Aliquam dictum pellentesque placerat. Duis mi nisl, sollicitudin ut molestie nec, pharetra sed dui.

Fusce nunc eros, rhoncus id porttitor non, tempor sed purus. Curabitur pretium gravida rhoncus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec sit amet ligula vitae lectus dapibus rhoncus et sed mauris. Curabitur mollis mollis dignissim. Aenean facilisis mauris aliquam diam eleifend nec tincidunt enim commodo. Integer mi nisl, ultricies sit amet scelerisque at, iaculis quis justo. Sed quis sagittis lorem. Sed accumsan est non leo porttitor rhoncus ac id ante. Sed auctor egestas varius. Curabitur condimentum mauris tortor, feugiat ornare dolor. Pellentesque porttitor metus quis diam sagittis sed ullamcorper ipsum mollis. Morbi eros neque, vulputate ut sollicitudin nec, mollis a lacus. Pellentesque quis lacus non ante imperdiet cursus.

Ut sit amet rhoncus quam. Phasellus orci nibh, viverra vel dictum et, lobortis sit amet enim. Ut luctus congue elit sed consectetur. Nullam ac metus nibh. Suspendisse vehicula eleifend ligula, eu blandit metus venenatis quis. Quisque mollis elit quis velit rutrum eget mollis erat sollicitudin. Vestibulum sit amet quam vitae quam ullamcorper facilisis non et eros. Aliquam malesuada leo eget erat commodo non hendrerit libero porttitor. Sed est massa, pulvinar pretium commodo vel, malesuada vel tellus. Donec porttitor placerat ultricies. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum at lectus a neque pharetra euismod eu id urna. Pellentesque nec elit sit amet ligula facilisis molestie.
""",
"""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent venenatis egestas libero condimentum convallis. Donec odio nibh, porttitor vel sodales nec, luctus ut dui. Mauris a ultrices mi. Praesent consectetur tincidunt ante sit amet sollicitudin. Praesent pretium elit id arcu iaculis eu varius odio eleifend. Suspendisse ac velit eu arcu vestibulum pharetra. In hac habitasse platea dictumst. Curabitur interdum commodo tempor. Vivamus vel mi eu dolor porta pretium sed eu erat.

Aenean gravida risus ac tellus lobortis varius. In sit amet leo a arcu sagittis scelerisque eget vitae libero. Vivamus accumsan est ac nibh venenatis feugiat. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed tortor ante, molestie eu blandit vel, fringilla in magna. Nullam orci libero, condimentum eget hendrerit ac, porttitor non enim. Etiam elit diam, hendrerit ac adipiscing quis, dictum in lectus. Morbi sed vehicula tortor. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In egestas, odio a facilisis molestie, dolor eros dictum orci, et viverra massa metus sed elit. Fusce ac ipsum justo, et bibendum sapien. Ut eros mi, vestibulum quis eleifend eget, dapibus vel felis. Proin dignissim justo in lectus venenatis et bibendum nisl feugiat. Fusce dictum mollis tempus. Curabitur velit est, viverra mattis mollis et, aliquam eget tellus.

Proin tempor, lorem nec elementum sodales, justo lectus tincidunt dolor, at rhoncus lacus metus eget diam. Aenean at fermentum sapien. Suspendisse lacinia elementum odio id dignissim. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec sollicitudin tempor nisi, nec porttitor justo pretium nec. Nulla facilisi. Etiam malesuada nulla in est dapibus vel mattis nulla suscipit. Duis tincidunt sagittis ante id tempor. Integer vel vestibulum eros. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
""",
"""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin consectetur pretium lectus. Nam rutrum tempus massa, in laoreet elit ornare at. Fusce facilisis ornare nisi, eget luctus arcu interdum et. Nulla vel dolor ante. Proin iaculis, sem ut fermentum scelerisque, risus massa tempus ipsum, et sodales nisl neque in tortor. Integer libero neque, malesuada a auctor a, tempor ac diam. Praesent lacinia tortor id orci sodales tincidunt. Sed commodo suscipit congue.

Nulla facilisi. Suspendisse sollicitudin, eros sodales dapibus pulvinar, urna lectus dignissim mi, in imperdiet eros arcu et ante. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Proin eget nisl magna. Suspendisse potenti. Sed euismod consequat odio nec tristique. Etiam vel turpis dui.

Nullam cursus sem semper mauris mollis pretium. Proin a lorem est. Donec vitae metus nibh, eu fermentum leo. Suspendisse eget orci libero, venenatis auctor velit. Praesent sit amet ligula quis elit adipiscing ultrices. Sed ac fermentum nisl. Donec sodales leo ut turpis interdum rutrum. Nam sed eros vel risus semper mollis.
"""
]
