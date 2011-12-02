import belaylibs.models as bcap
from django.db import models
import time
import logging
import sha

logger = logging.getLogger('default')

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
      password_hash=sha.new(admin_password).hexdigest(), full_name=admin_name,
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
  default_target = models.ForeignKey('DecisionValue', related_name='dt', null=True)
  default_decision = models.ForeignKey('DecisionValue', related_name='dd', null=True)
  display_component = models.ForeignKey('ComponentType', related_name='dc', null=True)
  name = models.TextField()
  shortname = models.TextField(unique=True)
  admin_contact = models.ForeignKey('User', related_name='ac', null=True)
  last_change = models.IntegerField(default=0)
  show_bid = models.BooleanField()
  show_num = models.BooleanField()
  general_text = models.TextField()
  component_text = models.TextField()
  use_ds = models.BooleanField()
  ds_cutoff_hi = models.FloatField(default=7.0)
  ds_cutoff_lo = models.FloatField(default=2.0)
  ds_conflict_cut = models.FloatField(default=0.05)

class Role(bcap.Grantable):
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
  targetable = models.BooleanField(default=True)
  abbr = models.CharField(max_length=1)
  description = models.TextField()
  conference = models.ForeignKey(Conference)

class ComponentType(bcap.Grantable):
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

class ReviewComponentType(bcap.Grantable):
  description = models.TextField()
  pc_only = models.BooleanField()
  conference = models.ForeignKey(Conference)

class User(bcap.Grantable):
  username = models.CharField(max_length=20)
  full_name = models.TextField()
  email = models.EmailField()
  password_hash = models.TextField()
  conference = models.ForeignKey(Conference)
  roles = models.ManyToManyField(Role)

class UnverifiedUser(bcap.Grantable):
  name = models.TextField()
  email = models.EmailField()
  # Note: this is directly from contwinue.py
  # role is not a foreign key to role, just a text field
  roletext = models.TextField(default='user')
  conference = models.ForeignKey(Conference)

class Topic(bcap.Grantable):
  name = models.TextField()
  papers = models.ManyToManyField('Paper')
  conference = models.ForeignKey(Conference)

class Paper(bcap.Grantable):
  contact = models.ForeignKey(User)
  author = models.TextField()
  title = models.TextField(default='No Paper Title Given')
  target = models.ForeignKey(DecisionValue)
  other_cats = models.BooleanField(default=True)
  pc_paper = models.BooleanField(default=False)
  hidden = models.BooleanField(default=False)
  conference = models.ForeignKey(Conference)
  json = models.TextField(default='')
  oscore = models.IntegerField(default=-3)

class Component(bcap.Grantable):
  type = models.ForeignKey(ComponentType)
  paper = models.ForeignKey(Paper)
  last_submitted = models.IntegerField()
  value = models.TextField()
  mimetype = models.TextField()
  conference = models.ForeignKey(Conference)

class DeadlineExtension(bcap.Grantable):
  type = models.ForeignKey(ComponentType)
  paper = models.ForeignKey(Paper)
  until = models.IntegerField()

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
