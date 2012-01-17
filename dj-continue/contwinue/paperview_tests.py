import belaylibs.dj_belay as bcap

import settings

import contwinue.models as m
from contwinue.reviewer import *

from contwinue.tests_common import Generator, has_keys, make_author

def make_reviewer(name, email, conf):
  user = make_author(name, email, conf)
  revrole = m.get_one(conf.role_set.filter(name='reviewer'))
  user.roles.add(revrole)
  return user

class TestGetByRole(Generator):
  def test_get_users(self):

    admin = m.get_one(m.Role.get_by_conf_and_name(self.conference, 'reviewer').user_set.all())
    r1 = make_reviewer('Reviewer', 'foo@bar.com', self.conference)
    get_users = bcap.grant('get-by-role', self.conference)
    result = get_users.post({'role': 'reviewer'})

    self.assertEqual(result, [
      admin.to_json(),
      r1.to_json()
    ])
