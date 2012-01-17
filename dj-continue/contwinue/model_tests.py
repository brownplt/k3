from contwinue.tests_common import Generator, make_reviewer, make_review
import contwinue.models as m

class TestPaperJsons(Generator):
  def test_dcomps(self):
    p = m.Paper.objects.all()[0]

    dc = p.dcomps
    self.assertEqual(dc, [])

    ct = m.get_one(m.ComponentType.objects.filter(abbr='P'))
    c = m.Component(
      type=ct,
      paper=p,
      lastSubmitted=1234,
      value='some/file',
      mimetype='application/pdf',
      conference=self.conference
    )
    c.save()

    dc = p.dcomps
    self.assertEqual(dc, [c])

  def test_reviews_info(self):
    p = m.Paper.objects.all()[0]

    revs = p.reviews_info
    self.assertEqual(revs, [])

    reviewer = make_reviewer(
      'Joe Reviewer',
      'joe@fake.bar',
      self.conference
    )
    review1 = make_review(self.conference, reviewer, p, True)
    review2 = make_review(self.conference, reviewer, p, False)

    revs = p.reviews_info
    self.assertEqual(len(revs), 2)
    self.assertItemsEqual(revs, [{
        'id': review1.id,
        'reviewerID': reviewer.id,
        'name': 'Joe Reviewer',
        'expertise': self.conference.default_expertise.abbr,
        'overall': self.conference.default_overall.abbr,
        'submitted': True
      }, {
        'id': review2.id,
        'reviewerID': reviewer.id,
        'name': 'Joe Reviewer',
        'expertise': self.conference.default_expertise.abbr,
        'overall': self.conference.default_overall.abbr,
        'submitted': False
      }
    ])

