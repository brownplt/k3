from contwinue.tests_common import Generator, make_reviewer, make_review
import contwinue.models as m
import belaylibs.dj_belay as bcap
import cjson as cjson
import random as random
from datetime import datetime

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
  def speed_test(self):
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
