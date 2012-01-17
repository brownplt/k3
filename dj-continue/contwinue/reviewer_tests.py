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
    loveto = m.get_one(m.BidValue.objects.filter(conference=self.conference, abbr='Q'))
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

class TestReviewPercentages(Generator):
  def test_get_percentages(self):
    def make_review(reviewer, paper, submitted):
      rev = m.Review(
        reviewer=reviewer,
        paper=paper,
        published=True,
        submitted=submitted,
        overall=self.conference.default_overall,
        expertise=self.conference.default_expertise,
        last_saved=0,
        conference=self.conference
      )
      rev.save()
      return rev
      
    [p1, p2] = m.Paper.objects.filter(conference=self.conference)[0:2]

    admin = m.get_one(m.Role.get_by_conf_and_name(self.conference, 'reviewer').user_set.all())
    r1 = make_reviewer('Bob Reviewer', 'bob@fake.org', self.conference)
    r2 = make_reviewer('Joe Reviewer', 'joe@foo.org', self.conference)

    rev1 = make_review(r1, p1, True)
    rev2 = make_review(r1, p2, False)
    rev3 = make_review(r2, p1, False)
    
    get_percents = bcap.grant('get-review-percentages', self.conference)
    result = get_percents.get()

    self.assertEqual(result, [
      {'id': admin.id, 'name': admin.full_name, 'percentage': 'N/A'},
      {'id': r1.id, 'name': r1.full_name, 'percentage': '50%'},
      {'id': r2.id, 'name': r2.full_name, 'percentage': '0%'}
    ])

