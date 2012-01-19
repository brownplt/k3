import belaylibs.dj_belay as bcap

import settings

import contwinue.models as m
from contwinue.reviewer import *

import time

from contwinue.tests_common import Generator, has_keys, make_author, \
    make_reviewer, make_review

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

class TestSaveReview(Generator):
  def test_review_save(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]
    rev = make_reviewer('Joe Reviewer', 'joe@fak.edu', self.conference)
    review = make_review(conf, rev, paper, False)

    rating = m.get_one(m.RatingValue.objects.filter(abbr='A'))
    expertise = m.get_one(m.ExpertiseValue.objects.filter(abbr='Y'))
    pc_comments = m.get_one(
      m.ReviewComponentType.objects.filter(pc_only=True)
    )
    author_comments = m.get_one(
      m.ReviewComponentType.objects.filter(pc_only=False)
    )

    save_review = bcap.grant('save-review', review)
    post_data = {
      'overallrating': rating.id,
      'expertiserating': expertise.id,
      'subreviewer': 'Dumpty, Humpty',
    }
    post_data['comp-%s' % pc_comments.id] = 'Honestly, pretty dumb'
    post_data['comp-%s' % author_comments.id] = \
      'Great work! Not this time'
    result = save_review.post(post_data)

    reviewafter = m.get_one(m.Review.objects.filter(id=review.id)).get_draft()

    self.assertEqual(reviewafter.overall.to_json(), rating.to_json())
    self.assertEqual(reviewafter.expertise, expertise)

    self.maxDiff=None
    self.assertEqual(result, reviewafter.to_json())

    pc_comp = m.get_one(m.ReviewComponent.objects.filter(
      review=reviewafter,
      type=pc_comments
    ))
    author_comp = m.get_one(m.ReviewComponent.objects.filter(
      review=reviewafter,
      type=author_comments
    ))
    self.assertEqual(pc_comp.value, 'Honestly, pretty dumb')
    self.assertEqual(author_comp.value, 'Great work! Not this time')

class TestGetReview(Generator):
  def test_get_review(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]
    rev = make_reviewer('Joe Reviewer', 'joe@fak.edu', self.conference)
    review = make_review(conf, rev, paper, False)

    reviews = m.Review.objects.filter(paper=paper)
    self.assertEqual(len(reviews), 1)

    get_review = bcap.grant('get-review', {'user': rev, 'paper': paper})
    result = get_review.get()

    # A draft should have been created
    reviews = m.Review.objects.filter(paper=paper)
    self.assertEqual(len(reviews), 2)

    draft = m.get_one(m.Review.objects.filter(
      paper=paper,
      published=False
    ))

    self.assertEqual(result, {
      'hasPublished': False,
      'review': draft.to_json()
    })

  def test_get_no_review(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]
    rev = make_reviewer('Joe Reviewer', 'joe@fak.edu', conf)
    get_review = bcap.grant('get-review', {'user': rev, 'paper': paper})
    result = get_review.get()
    
    self.assertEqual(result, False)

class TestRevertReview(Generator):
  def test_revert_review(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]
    rev = make_reviewer('Joe Reviewer', 'joe@fak.edu', self.conference)
    review = make_review(conf, rev, paper, False)
    draft = review.make_draft()

    rating = m.get_one(m.RatingValue.objects.filter(abbr='A'))
    draft.overall = rating
    draft.save()
    pc_comments = m.get_one(
      m.ReviewComponentType.objects.filter(pc_only=True)
    )
    comp = m.ReviewComponent(conference=conf,review=draft,type=pc_comments,value='stuff')
    comp.save()

    self.maxDiff = None
    revert_cap = bcap.grant('revert-review', review)
    response = revert_cap.post()

    draft2 = review.get_draft()
    self.assertEqual(draft2.overall, conf.default_overall)
    self.assertEqual(len(draft2.reviewcomponent_set.all()), 0)
    self.assertEqual(response, {
      'hasPublished': False,
      'review': draft2.to_json()
    })

class TestSetHidden(Generator):
  def test_set_hidden(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]
    self.assertEqual(paper.hidden, False)

    hide_cap = bcap.grant('set-hidden', paper)
    hide_cap.post({'hidden': 'yes'})

    paper2 = m.Paper.objects.all()[0]
    self.assertEqual(paper2.hidden, True)

class TestSetDeadline(Generator):
  def test_set_deadline(self):
    conf = self.conference
    paper = m.Paper.objects.all()[0]

    self.assertEqual(len(paper.deadlineextension_set.all()), 0)

    extension = int(time.time()) + 10000
    typ = m.get_one(m.ComponentType.objects.filter(abbr='P'))

    extend = bcap.grant('set-deadline', paper)
    result = extend.post({'typeid': typ.id, 'until': extension})

    paper = m.Paper.objects.all()[0]
    exts = paper.deadlineextension_set.all()
    self.assertEqual(len(exts), 1)
    self.assertEqual(int(exts[0].until), int(extension))
    self.assertEqual(result, exts[0].to_json())

    extension2 = int(time.time()) + 30000
    result2 = extend.post({'typeid': typ.id, 'until': extension2})
    paper = m.Paper.objects.all()[0]
    exts = paper.deadlineextension_set.all()
    self.assertEqual(len(exts), 1)
    self.assertEqual(int(exts[0].until), int(extension2))
    self.assertEqual(result2, exts[0].to_json())

