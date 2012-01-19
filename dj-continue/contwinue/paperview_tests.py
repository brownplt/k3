import belaylibs.dj_belay as bcap

import settings

import contwinue.models as m
from contwinue.reviewer import *

from contwinue.tests_common import Generator, has_keys, make_author, \
    make_reviewer

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

class TestGetPaper(Generator):
  def test_get_paper(self):
    p1 = m.Paper.objects.all()[0]
    get_paper = bcap.grant('get-paper', p1)
    self.assertEqual(get_paper.get(), p1.get_paper_with_decision())


    
