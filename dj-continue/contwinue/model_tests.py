from contwinue.tests_common import Generator, make_reviewer, make_review
import contwinue.models as m
import belaylibs.dj_belay as bcap
import cjson as cjson
import random as random
from datetime import datetime

class TestPaperJsons(Generator):
  def setUp(self):
    super(TestPaperJsons, self).setUp()
    self.p = m.Paper.objects.all()[0]
    self.r = m.get_one(m.Role.objects.filter(name='reviewer'))
    self.rev = self.r.user_set.all()[0]
    self.protected_type = m.get_one(m.ComponentType.objects.filter(abbr='V'))

  def test_dcomps(self):
    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])

    ct = m.get_one(m.ComponentType.objects.filter(abbr='P'))
    c = m.Component(
      type=ct,
      paper=self.p,
      lastSubmitted=1234,
      value='some/file',
      mimetype='application/pdf',
      conference=self.conference
    )
    c.save()

    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [c])

  def test_dcomps_protected(self):
    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])

    c = m.Component(
      type=self.protected_type,
      paper=self.p,
      lastSubmitted=1234,
      value='some/file',
      mimetype='application/pdf',
      conference=self.conference
    )
    c.save()

    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])

  def test_dcomps_granted_not_approved(self):
    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])
    
    c = m.Component(
      type=self.protected_type,
      paper=self.p,
      lastSubmitted=1234,
      value='some/file',
      mimetype='application/pdf',
      conference=self.conference
    )
    c.save()

    grant_request = m.ComponentGrantRequest(
      reviewer=self.rev,
      component=c,
      granted=False,
      conference=self.rev.conference
    )
    grant_request.save()

    # stil not present
    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])

  def test_dcomps_granted_and_approved(self):
    dc = self.p.get_dcomps_safe(self.rev)
    self.assertEqual(dc, [])
    
    c = m.Component(
      type=self.protected_type,
      paper=self.p,
      lastSubmitted=1234,
      value='some/file',
      mimetype='application/pdf',
      conference=self.conference
    )
    c.save()

    grant_request = m.ComponentGrantRequest(
      reviewer=self.rev,
      component=c,
      granted=True,
      conference=self.rev.conference
    )
    grant_request.save()

    # now it's present
    dc = self.p.get_dcomps_safe(self.rev)
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

def transform(obj):
  if isinstance(obj, bcap.Capability):
    return {'@': obj.serialize()}
  elif isinstance(obj, dict):
    for k, v in obj.iteritems():
      obj[k] = transform(v)
    return obj 
  elif isinstance(obj, list):
    return map(lambda o: transform(o), obj)
  elif hasattr(obj, 'to_json'):
    return obj.to_json()
  else:
    return obj

class TestCJSONSpeed(Generator):
  def test_speed(self):
    obj = {}
    for i in range(0,100):
      for c in range(33,126):
        if i % 2 == 0:
          obj[str(str(i) + chr(c))] = bcap.Capability(str(random.randint(0,500000)))
        else:
          obj[str(str(i) + chr(c))] = {'just': True, 'some': 0, 'data': 'str'}

    t1 = datetime.now()
    foo = bcap.dataPreProcess(obj)
    t2 = datetime.now()

    print('Diff: %s', t2 - t1)

    t1 = datetime.now()
    objchanged = transform(obj)
    foo2 = cjson.encode(obj)
    t2 = datetime.now()
    
    print('Diff: %s', t2 - t1)

class TestMeetingOrder(Generator):
  def setup_meeting(self):
    [p3, p2, p1] = m.Paper.objects.all()[:3]
    m.MeetingOrder.set_order(
      conf=self.conference,
      papers=" ".join([str(p.id) for p in [p1, p2, p3]])
    )
    self.p1, self.p2, self.p3 = p1, p2, p3

  def test_set_order(self):
    self.setup_meeting()
    mos = m.MeetingOrder.objects.all()
    self.assertEqual(mos[0].paper.id, self.p1.id)
    self.assertEqual(mos[0].morder, 1)
    
    self.assertEqual(mos[1].paper.id, self.p2.id)
    self.assertEqual(mos[1].morder, 2)

    self.assertEqual(mos[2].paper.id, self.p3.id)
    self.assertEqual(mos[2].morder, 3)

  def test_set_twice(self):
    self.setup_meeting()
    mo = m.MeetingOrder.objects.all()[0]
    mo.current = True
    mo.save()
    with self.assertRaises(m.MeetingException):
      self.setup_meeting()

  def test_jump_to(self):
    self.setup_meeting()
    m.MeetingOrder.jump_to(self.conference, str(self.p2.id))
    mo = m.get_one(m.MeetingOrder.objects.filter(current=True))
    self.assertEqual(mo.paper, self.p2)
    m.MeetingOrder.jump_to(self.conference, str(self.p1.id))
    mo = m.get_one(m.MeetingOrder.objects.filter(current=True))
    self.assertEqual(mo.paper, self.p1)

  def test_jump_bad(self):
    self.setup_meeting()
    with self.assertRaises(m.MeetingException):
      m.MeetingOrder.jump_to(self.conference, str(-1))

  def test_get_order(self):
    self.setup_meeting()
    order = m.MeetingOrder.get_order(self.conference)
    self.assertEqual(len(order), 3)
    self.assertEqual(order[0]['paperID'], self.p1.id)
    self.assertEqual(order[1]['paperID'], self.p2.id)
    self.assertEqual(order[2]['paperID'], self.p3.id)

  def test_get_paper(self):
    self.setup_meeting()
    paper = m.MeetingOrder.get_paper(self.conference, self.p2.id)
    pjson = self.p2.get_paper()
    for prop in ['id','title','author','target','othercats']:
      self.assertEqual(paper[prop], pjson[prop])
    self.assertEqual(paper['decision'], self.p2.decision.to_json())
    self.assertEqual(paper['conflicts'], self.p2.conflicts)
    self.assertEqual(paper['reviewsInfo'], self.p2.reviews_info)

  def test_end_meeting(self):
    self.setup_meeting()
    m.MeetingOrder.jump_to(self.conference, self.p2.id)
    mo = m.get_one(m.MeetingOrder.objects.filter(current=True))
    self.assertEqual(mo.paper, self.p2)
    m.MeetingOrder.end_meeting(self.conference)
    mo = m.get_one(m.MeetingOrder.objects.filter(current=True))
    self.assertEqual(mo, None)

