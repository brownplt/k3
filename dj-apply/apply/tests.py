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

class TestScoreCategory(unittest.TestCase):
  def setUp(self):
    depts = Department.objects.filter(name='Computer Science')
    if len(depts) == 0:
      cs = Department(name='Computer Science', shortname='CS', lastChange=0,\
        headerImage='', logoImage='', resumeImage='', headerBgImage='',\
        brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
        techEmail='tech@example.com')
      cs.save()
      self.department = cs

  def testScoreCategory(self):
    args = {\
      'name' : 'Category Uno',\
      'shortform' : 'CU',\
      'department' : 'Computer Science'\
    }

    addHandler = SCAddHandler()
    response = bcap.dataPostProcess(addHandler.post(None, args).content)

    hasChange = response.has_key('change')
    hasDelete = response.has_key('delete')
    self.assertTrue(hasChange and hasDelete and response['success'])

    
    cats = ScoreCategory.objects.filter(name='Category Uno', shortform='CU',\
      department=self.department)
    self.assertEqual(len(cats), 1)
