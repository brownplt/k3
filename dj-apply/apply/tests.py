import unittest
from apply.models import *
from apply.views import *

import belaylibs.dj_belay as bcap

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
    init = ApplyInit()
    init.process_request(None)

  def testReviewerRequest(self):
    request_cap = bcap.grant('request-new-reviewer', self.department)    

    create_cap = request_cap.post({
      'name': 'Fake Reviewer',
      'email': 'reviewer@fake',
      'committee': 'true'
    })
    create_cap.post({})
    info = AuthInfo.objects.filter(email="reviewer@fake")
    self.assertEqual(len(info), 1)
    revs = Reviewer.objects.filter(auth=info[0])
    self.assertEqual(revs[0].committee, False)

    # The capability to create shouldn't work twice
    try:
      create_cap.post({})
      self.assertTrue(False)
    except:
      self.assertTrue(True)
