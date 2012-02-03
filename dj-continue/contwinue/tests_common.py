import uuid

from contwinue.views import ContinueInit
from contwinue.models import Conference, Account, User, get_one, \
  Review, Role, Paper
from contwinue.test_generate import generate

from django.test import TestCase

class Generator(TestCase):
  def setUp(self):
    generate()
    init = ContinueInit()
    init.process_request(None)
    self.conference = Conference.get_by_shortname('SC')
    admin_role = get_one(Role.objects.filter(name='admin'))
    self.admin = admin_role.user_set.all()[0]
    reviewer_role = get_one(Role.objects.filter(name='reviewer'))
    self.reviewers = reviewer_role.user_set.all()
    self.papers = Paper.objects.all()

  def tearDown(self):
    self.conference.delete()

def has_keys(d, keys):
  return all([d.has_key(k) for k in keys])

def make_author(full_name, email, conference):
  account = Account(key=str(uuid.uuid4()))
  account.save()
  user = User(
    full_name=full_name,
    email=email,
    conference=conference,
    account=account
  )
  user.save()
  return user

def make_reviewer(name, email, conf):
  user = make_author(name, email, conf)
  revrole = get_one(conf.role_set.filter(name='reviewer'))
  user.roles.add(revrole)
  return user

def make_review(conf, reviewer, paper, submitted):
  rev = Review(
    reviewer=reviewer,
    paper=paper,
    published=True,
    submitted=submitted,
    overall=conf.default_overall,
    expertise=conf.default_expertise,
    last_saved=0,
    conference=conf
  )
  rev.save()
  return rev



