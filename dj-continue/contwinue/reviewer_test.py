import belaylibs.dj_belay as bcap

import settings

import contwinue.models as m
from contwinue.reviewer import *

from contwinue.tests_common import Generator, has_keys, make_author

class TestGetPaperSummaries(Generator):
  def test_get_summaries(self):
    user = make_author('Joe Reviewer', 'joe@fake.org', self.conference)
    revrole = get_one(self.conference.role_set.filter(name='reviewer'))
    user.roles.add(revrole)

#    get_sums = bcap.grant('get-paper-summaries', user)
#    result = get_sums.post({'lastChange: 0'})

#    self.assertEqual(len(result['summaries']), 11)
#    self.assertEqual(result['changed'], True)

class TestGetAbstracts(Generator):
  def test_get_abstracts(self):
    p = m.Paper.objects.filter(conference=self.conference)[0]

    get_abstracts = bcap.grant('get-abstracts', self.conference)
    abstracts = get_abstracts.get()

    self.assertEqual(len(abstracts), 10)
    for i in range(0,10):
      self.assertEqual(abstracts[i]['value'], "Paper %s abstract" % abstracts[i]['id'])

