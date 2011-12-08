import belaylibs.models as bcap
from django.db import models
import time
import logging
import sha

logger = logging.getLogger('default')

def convertTime(secs):
	return time.strftime("%A, %B %d, %Y %I:%M %p GMT",time.gmtime(secs))

class FoundMoreThanOneException(Exception):
  pass

def get_one(query_dict):
  if len(query_dict) == 0: return None
  elif len(query_dict) == 1: return query_dict[0]
  else: raise FoundMoreThanOneException('Found more than one')

class Conference(bcap.Grantable):
  @classmethod
  def make_new(cls, name, shortname, admin_user, admin_password, admin_name, admin_email, use_ds):
    c = Conference(
      name=name,
      shortname=shortname,
      last_change=int(time.time()),
      show_bid=True,
      show_num=False,
      general_text='',
      component_text='',
      use_ds=use_ds)
    c.save()

    admin_role = Role(conference=c, name='admin')
    admin_role.save()
    reviewer_role = Role(conference=c, name='reviewer')
    reviewer_role.save()
    user_role = Role(conference=c,name='user')
    user_role.save()

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

    undecided = DecisionValue(conference=c, abbr='U', targetable=False, 
      description='Undecided')
    undecided.save()
    rejected = DecisionValue(conference=c, abbr='R', targetable=False, 
      description='Rejected')
    rejected.save()
    accepted = DecisionValue(conference=c, abbr='A', targetable=True, 
      description='Accepted')
    accepted.save()

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

    if use_ds:
      for n in range(10):
        if n == 9:
          description = 'Highest'
        elif n == 0:
          description = 'Lowest'
        else:
          description = ''
        rv = RatingValue(conference=c, abbr=str(n),
          description=description, number=n)
        rv.save()
    else:
      rv = RatingValue(conference=c, abbr='A',
        description='Good paper. I will champion it at the PC meeting.',
        number=4)
      rv.save()
      rv = RatingValue(conference=c, abbr='B',
        description='OK paper, but I will not champion it.', number=3)
      rv.save()
      rv = RatingValue(conference=c, abbr='C',
        description='Weak paper, though I will not fight strongly against it.',
        number=2)
      rv.save()
      rv = RatingValue(conference=c, abbr='D',
        description='Serious problems. I will argue to reject this paper.',
        number=1)
      rv.save()
    no_rate = RatingValue(conference=c, abbr='U',
      description='Rating not specified.', number=-1)
    no_rate.save()

    no_exp = ExpertiseValue(conference=c, abbr='F',
      description='Expertise not specified.', number=3)
    no_exp.save()
    ev = ExpertiseValue(conference=c, abbr='X',
      description='I am an expert in the subject area.',
      number=5)
    ev.save()
    ev = ExpertiseValue(conference=c, abbr='Y',
      description='I am knowledgeable in the area, though not an expert.',
      number=4)
    ev.save()
    ev = ExpertiseValue(conference=c, abbr='Z',
      description='I am not an expert. My evaluation is that of an informed\
        outsider.',
      number=3)
    ev.save()

    # Deadline is 30 days from submission
    abstract = ComponentType(conference=c, abbr='A', description='Abstract', 
      fmt='Text', deadline=int(time.time())+(86400*30), mandatory=True,
      grace_hours=0, size_limit=0)
    abstract.save()
    paper = ComponentType(conference=c, abbr='P', description='Paper',
      fmt='PDF', deadline=int(time.time())+(86400*30), mandatory=True,
      grace_hours=0, size_limit=0)
    paper.save()

    adm = User(conference=c, username=admin_user, 
      full_name=admin_name,
      email=admin_email)
    # 2 saves because you can't add ManyToMany relationships until the instance
    # is saved
    adm.save()
    adm.roles.add(admin_role)
    adm.roles.add(reviewer_role)
    adm.save()

    c.admin_contact = adm
    c.default_bid = no_bid
    c.conflict_bid = conf_bid
    c.default_overall = no_rate
    c.default_expertise = no_exp
    c.default_target = accepted
    c.default_decision = undecided
    c.display_component = abstract
    c.save()

    return c

  default_bid = models.ForeignKey('BidValue', related_name='db', null=True)
  conflict_bid = models.ForeignKey('BidValue', related_name='cb', null=True)
  default_overall = models.ForeignKey('RatingValue', related_name='do', null=True)
  default_expertise = models.ForeignKey('ExpertiseValue', related_name='de', null=True)
  default_target = models.ForeignKey('DecisionValue', related_name='dt',\
    null=True, on_delete=models.SET_NULL)
  default_decision = models.ForeignKey('DecisionValue', related_name='dd',\
    null=True, on_delete=models.SET_NULL)
  display_component = models.ForeignKey('ComponentType', related_name='dc',\
    null=True, on_delete=models.SET_NULL)
  name = models.TextField()
  shortname = models.TextField(unique=True)
  admin_contact = models.ForeignKey('User', related_name='ac', null=True,\
    on_delete=models.SET_NULL)
  last_change = models.IntegerField(default=0)
  show_bid = models.BooleanField()
  show_num = models.BooleanField()
  general_text = models.TextField()
  component_text = models.TextField()
  use_ds = models.BooleanField()
  ds_cutoff_hi = models.FloatField(default=7.0)
  ds_cutoff_lo = models.FloatField(default=2.0)
  ds_conflict_cut = models.FloatField(default=0.05)

  def my(self, cls):
    return cls.objects.filter(conference=self)
  def get_title_and_contact(self):
    return {
      'info' : {
        'name': self.name,
        'shortname' : self.shortname
      },
      'adminContact' : self.admin_contact.email
    }
  @classmethod
  def get_by_shortname(cls, shortname):
    items = Conference.objects.filter(shortname=shortname)
    return get_one(items)

  def get_writer_basic(self):
    decisions = self.my(DecisionValue)
    decision_json = [d.to_json() for d in decisions if d.targetable]
    components = self.my(ComponentType)
    component_json = [c.to_json() for c in components]
    topics = self.my(Topic)
    topic_json = [t.to_json() for t in topics]
    info = {
      'showNum': self.show_num,
      'name': self.name,
      'shortname': self.shortname
    }
    return {
      'decisions': decision_json,
      'components': component_json,
      'topics': topic_json,
      'info': info
    }

  def get_author_text(self):
    return [self.general_text, self.component_text]

  def get_topics(self): return self.my(Topic)

  def get_topic_by_name(self, name):
    return get_one(self.my(Topic).filter(name=name))

  def has_topic_named(self, name):
    return len(self.my(Topic).filter(name=name)) > 0

  def has_component_type(self, abbr):
    return len(self.my(ComponentType).filter(abbr=abbr)) > 0

  def component_type_by_abbr(self, abbr):
    return get_one(ComponentType.objects.filter(conference=self, abbr=abbr))

  def has_decision_value(self, targetable, abbr, description):
    return len(self.my(DecisionValue).filter(targetable=targetable, abbr=abbr,\
      description=description, conference=self)) > 0

  def get_decision_value(self, targetable, abbr, description):
    return get_one(DecisionValue.objects.filter(targetable=targetable,\
      abbr=abbr, description=description, conference=self))

  def has_rc_type(self, description, pc_only):
    return len(self.my(ReviewComponentType).filter(description=description,\
      pc_only=pc_only, conference=self)) > 0

  def get_rc_type(self, description, pc_only):
    return get_one(ReviewComponentType.objects.filter(description=description,\
      pc_only=pc_only, conference=self))

  def update_last_change(self,paper=None):
    self.lastChange = int(time.time())
    if paper == None:
      pl = Paper.objects.filter(conference=self)
    else:
      pl = [paper]
    for p in pl:
      p.json = ''

  def get_admin(self):
    return {
      # TODO(matt): name? username? email?
      'adminContact' : self.admin_contact.email,
      'dsCutoffHi' : self.ds_cutoff_hi,
      'dsCutoffLo' : self.ds_cutoff_lo,
      'dsConflictCut' : self.ds_conflict_cut
    }

  def get_all(self):
    return [u.to_json() for u in self.my(User)]

  def papers_of_dv(self, decision_value):
    return [p.id for p in self.my(Paper).filter(target=decision_value)]

class Role(bcap.Grantable):
  class Meta:
    unique_together = (('name', 'conference'))
  name = models.CharField(max_length=20)
  conference = models.ForeignKey(Conference)

class BidValue(bcap.Grantable):
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  conference = models.ForeignKey(Conference)

class RatingValue(bcap.Grantable):
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  number = models.IntegerField()
  conference = models.ForeignKey(Conference)

class ExpertiseValue(bcap.Grantable):
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  number = models.IntegerField()
  conference = models.ForeignKey(Conference)

class DecisionValue(bcap.Grantable):
  class Meta:
    unique_together = (('targetable', 'abbr', 'description', 'conference'))
  targetable = models.BooleanField(default=True)
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  conference = models.ForeignKey(Conference)
  
  def to_json(self):
    return {
      'id': self.id,
      'abbr': self.abbr,
      'description': self.description,
      'targetable': self.targetable
    }

class ComponentType(bcap.Grantable):
  class Meta:
    unique_together = (('abbr', 'conference'))
  def deadline_str(self):
	  return time.strftime("%A, %B %d, %Y %I:%M %p GMT", 
      time.gmtime(self.deadline))
  formats = [('Text', 'Text'), ('PDF', 'PDF'), ('Any', 'Any')]
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  fmt = models.TextField(choices=formats)
  size_limit = models.IntegerField()
  deadline = models.IntegerField()
  grace_hours = models.IntegerField()
  mandatory = models.BooleanField()
  conference = models.ForeignKey(Conference)

  def to_json(self):
    return {
      'id': self.id,
      'format': self.fmt,
      'description': self.description,
      'abbr': self.abbr,
      'sizelimit': self.size_limit,
      'deadline': self.deadline,
      'deadlineStr': self.deadline_str(),
      'mandatory': self.mandatory,
      'gracehours': self.grace_hours,
    }

class ReviewComponentType(bcap.Grantable):
  class Meta:
    unique_together = (('description', 'conference', 'pc_only'))
  description = models.TextField()
  pc_only = models.BooleanField()
  conference = models.ForeignKey(Conference)

  def to_json(self):
    return {
      'description' : self.description,
      'pcOnly' : self.pc_only
    }

class Launchable(): pass
class Account(bcap.Grantable):
  email = models.TextField(max_length=100)
  key = models.TextField(max_length=36)

  def get_launchables(self):
    launchables = [l.to_json() for l in Launchable.objects.filter(account=self)]
    return launchables

  def get_credentials(self):
    googles = []
    contwinues = []
    google = get_one(GoogleCredentials.objects.filter(account=self))
    if not (google is None): googles.append(google)
    for contwinue in ContinueCredentials.objects.filter(account=self):
      if not (contwinue is None): contwinues.append(contwinue)
    return {
      'googleCreds': [g.to_json() for g in googles],
      'continueCreds': [c.to_json() for c in contwinues]
    }

class User(bcap.Grantable):
  username = models.CharField(max_length=30)
  full_name = models.TextField()
  email = models.EmailField(unique=True)
  conference = models.ForeignKey(Conference)
  roles = models.ManyToManyField(Role)
  accounts = models.ManyToManyField(Account)

  def role_names(self):
    return [r.name for r in self.roles.all()]

  def to_json(self):
    review_count = len(Review.objects.filter(
      conference=self.conference, 
      reviewer=self, 
      published=True))
    return {
      'username' : self.username,
      'fullname' : self.full_name,
      'email' : self.email,
      'rolenames' : self.role_names(),
      'reviewCount' : review_count
    }

  def get_credentials(self):
    googles = []
    contwinues = []
    for account in self.accounts.all():
      google = get_one(GoogleCredentials.objects.filter(account=account))
      if not (google is None): googles.append(google)
      contwinue = get_one(ContinueCredentials.objects.filter(account=account))
      if not (contwinue is None): contwinues.append(contwinue)
    return {
      'googleCreds': [g.to_json() for g in googles],
      'continueCreds': [c.to_json() for c in contwinues]
    }

  def get_papers(self):
    return sorted(Paper.objects.filter(contact=self), key=lambda p: p.id)

class UnverifiedUser(bcap.Grantable):
  name = models.TextField()
  email = models.EmailField()
  # Note: this is directly from contwinue.py
  # role is not a foreign key to role, just a text field
  roletext = models.TextField(default='user')
  conference = models.ForeignKey(Conference)

class Topic(bcap.Grantable):
  class Meta:
    unique_together = (('conference', 'name'))

  name = models.TextField()
  papers = models.ManyToManyField('Paper')
  conference = models.ForeignKey(Conference)

  def to_json(self):
    return {
      'id': self.id,
      'name': self.name
    }

  @classmethod
  def get_by_conference_and_id(cls, conf, id):
    return Topic.objects.filter(id=id, conference=conf)

class Paper(bcap.Grantable):
  contact = models.ForeignKey(User)
  authors = models.ManyToManyField(User, related_name='authors')
  author = models.TextField()
  title = models.TextField(default='No Paper Title Given')
  target = models.ForeignKey(DecisionValue)
  other_cats = models.BooleanField(default=True)
  pc_paper = models.BooleanField(default=False)
  hidden = models.BooleanField(default=False)
  conference = models.ForeignKey(Conference)
  json = models.TextField(default='')
  oscore = models.IntegerField(default=-3)

  def my(self, cls):
    return cls.objects.filter(paper=self)

  def get_paper(self):
    paper_json = {
      'id': self.id,
      'othercats': self.other_cats,
      'pcpaper': self.pc_paper,
      'title': self.title,
      'target': self.target.to_json(),
      'author': self.author,
      'topics': [t.to_json() for t in self.topic_set.all()],
      'components': [c.to_json() for c in self.my(Component)]
    }
    return paper_json

  def get_deadline_extensions(self):
    return [ext.to_json() for ext in
            DeadlineExtension.objects.filter(paper=self)]

  def update_target_by_id(self, targetID):
    target = DecisionValue.objects.filter(id=targetID, targetable=True)
    if len(target) == 0: return None
    else: self.target = target[0]
    return None

  def update_othercats(self, othercats):
    if othercats == 'yes':
      self.other_cats = True
    else:
      self.other_cats = False
    return None

class Component(bcap.Grantable):
  type = models.ForeignKey(ComponentType)
  paper = models.ForeignKey(Paper)
  lastSubmitted = models.IntegerField()
  value = models.TextField()
  mimetype = models.TextField()
  conference = models.ForeignKey(Conference)

  def to_json(self):
    return {
      'typeID': self.type.id,
      'lsStr': convertTime(self.lastSubmitted),
      'value': self.value
    }

class DeadlineExtension(bcap.Grantable):
  type = models.ForeignKey(ComponentType)
  paper = models.ForeignKey(Paper)
  until = models.IntegerField()
  conference = models.ForeignKey(Conference)

  def to_json(self):
    return {
      'typeID': self.type.id,
      'paperID': self.paper.id,
      'until': self.until,
      'untilStr': convertTime(self.until)
    }

  @classmethod
  def get_by_ct_and_paper(self, ct, paper):
    des = DeadlineExtension.objects.filter(type=ct, paper=paper)
    return get_one(des)

class ReviewComponent(bcap.Grantable):
  type = models.ForeignKey(ReviewComponentType)
  review = models.ForeignKey('Review')
  value = models.TextField()
  conference = models.ForeignKey(Conference)

class Review(bcap.Grantable):
  reviewer = models.ForeignKey(User)
  paper = models.ForeignKey(Paper)
  submitted = models.BooleanField(default=False)
  published = models.BooleanField(default=False)
  overall = models.ForeignKey(RatingValue)
  experties = models.ForeignKey(ExpertiseValue)
  subreviewers = models.TextField(default='')
  last_saved = models.IntegerField()
  conference = models.ForeignKey(Conference)

# For accounts...

class Launchable(bcap.Grantable):
  account = models.ForeignKey(Account)
  launchbase = models.TextField(max_length=500)
  launchcap = models.TextField(max_length=500)
  display = models.TextField(max_length=1000)

  def to_json(self):
    return {
      'launchbase': self.launchbase,
      'launchcap': self.launchcap,
      'display': self.display
    }

class PendingAccount(bcap.Grantable):
  email = models.TextField(max_length=100)

class PendingLogin(bcap.Grantable):
  # Key is for this server to trust the openID provider's request
  key = models.CharField(max_length=36)
  # ClientKey is a secret provided by the client to trust that new
  # windows were served from this server
  clientkey = models.CharField(max_length=36)

class GoogleCredentials(bcap.Grantable):
  identity = models.CharField(max_length=200)
  account = models.ForeignKey(Account)

  def to_json(self):
    return {
      'email': self.account.email
    }

class ContinueCredentials(bcap.Grantable):
  username = models.CharField(max_length=200)
  salt = models.CharField(max_length=200)
  hashed_password = models.CharField(max_length=200)
  account = models.ForeignKey(Account)

  def to_json(self):
    return {
      'username': self.username,
      'email': self.account.email
    }
