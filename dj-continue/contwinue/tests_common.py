import uuid

from contwinue.views import ContinueInit
from contwinue.models import Conference, Account, User
from contwinue.generate import generate

from django.test import TestCase

class Generator(TestCase):
  def setUp(self):
    generate()
    init = ContinueInit()
    init.process_request(None)
    self.conference = Conference.get_by_shortname('SC')

  def tearDown(self):
    Conference.get_by_shortname('SC').delete()

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



