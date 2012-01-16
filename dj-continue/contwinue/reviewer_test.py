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

class TestGetPaperSummaries(Generator):
  def test_get_summaries(self):
    user = make_reviewer('Joe Reviewer', 'joe@fake.org', self.conference)

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

class TestUpdateBids(Generator):
  def test_update(self):
    user = make_reviewer('Bob Reviewer', 'bob@fake.org', self.conference)

    [p1, p2] = m.Paper.objects.filter(conference=self.conference)[0:2]

    self.assertEqual(len(m.Bid.objects.filter(paper=p1)), 0) 
    self.assertEqual(len(m.Bid.objects.filter(paper=p2)), 0) 

    ifneeded = m.get_one(m.BidValue.objects.filter(conference=self.conference, abbr='R'))
    loveto = m.get_one(m.BidValue.objects.filter(conference=self.conference, abbr='R'))
    b = m.Bid(paper=p1, conference=self.conference, bidder=user, value=loveto)
    b.save()

    self.assertEqual(len(m.Bid.objects.filter(paper=p1)), 1) 

    update_json = { 'bid': ifneeded.id, 'papers': [p1.id, p2.id] }

    update_bids = bcap.grant('update-bids', user)
    result = update_bids.post(update_json)

    [p1prime, p2prime] = m.Paper.objects.filter(conference=self.conference)[0:2]

    b1 = m.get_one(m.Bid.objects.filter(paper=p1))
    b2 = m.get_one(m.Bid.objects.filter(paper=p2))

    self.assertEqual(result, [b1.to_json(), b2.to_json()])

    self.assertEqual(b1.value, ifneeded) 
    self.assertEqual(b2.value, ifneeded) 

    self.assertEqual(b1.bidder, user)
    self.assertEqual(b2.bidder, user)
