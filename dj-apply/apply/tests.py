import unittest
from apply.models import *
from apply.views import *

import belaylibs.dj_belay as bcap

class UselessTest(unittest.TestCase):
  def setUp(self):
    pass

  def testUseless(self):
    self.assertEqual('true', 'true')


class TestNewReviewer(unittest.TestCase):
  def setUp(self):
    department = Department(
      name="Brown Department of Horticulture", \
      shortname="bhort", \
      lastChange=0, \
      brandColor="blue", \
      contactName="No one", \
      contactEmail="fake@fake", \
      techEmail="fake@bar")
    department.save()
    self.department = department

  def testReviewerRequest(self):
    request_cap = bcap.grant('request-new-reviewer', self.department)    
    create_cap = request_cap.post({
      'name': 'Fake Reviewer',
      'email': 'reviewer@fake',
      'committee': 'true'
    })
    create_cap.post({})
    info = AuthInfo.objects.filter(email="reviewer@fake")
    assertEqual(len(info), 1)
    revs = Reviewer.objects.filter(auth=info[0])
    assertEqual(revs[0].committee, True)
