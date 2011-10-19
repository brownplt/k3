import unittest
from apply.models import *
from apply.views import *

import belaylibs.dj_belay as bcap

class ApplyTest(unittest.TestCase):
  def makeCSDept(self):
    cs = Department(name='Computer Science', shortname='CS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
    self.department = cs
  def setUp(self):
    init = ApplyInit()
    init.process_request(None)

class TestNewReviewer(ApplyTest):
  def setUp(self):
    super(TestNewReviewer, self).setUp()
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
    self.assertEqual(len(info), 1)
    revs = Reviewer.objects.filter(auth=info[0])
    self.assertEqual(revs[0].committee, False)

    # The capability to create shouldn't work twice
    try:
      create_cap.post({})
      self.assertTrue(False)
    except:
      self.assertTrue(True)

class TestScoreCategory(ApplyTest):
  def setUp(self):
    super(TestScoreCategory, self).setUp()
    self.makeCSDept()

  def testScoreCategory(self):
    args = {\
      'name' : 'Category Uno',\
      'shortform' : 'CU',\
      'department' : 'Computer Science'\
    }

    addCap = bcap.grant('sc-add', None)
    response = addCap.post(args)

    hasChange = response.has_key('change')
    hasDelete = response.has_key('delete')
    self.assertTrue(hasChange and hasDelete and response['success'])
    
    cats = ScoreCategory.objects.filter(name='Category Uno', shortform='CU',\
      department=self.department)
    self.assertEqual(len(cats), 1)

    changeCap = response['change']
    changeCap.post({\
      'name' : 'Category Dos',\
      'shortform' : 'CD'\
    })
    cats = ScoreCategory.objects.filter(name='Category Uno', shortform='CU',\
      department=self.department)
    self.assertEqual(len(cats), 0)
    cats = ScoreCategory.objects.filter(name='Category Dos', shortform='CD',\
      department=self.department)
    self.assertEqual(len(cats), 1)

    delCap = response['delete']
    delResponse = delCap.delete()
    cats = ScoreCategory.objects.filter(name='Category Dos', shortform='CD',\
      department=self.department)
    self.assertEqual(len(cats), 0)

  def tearDown(self):
    self.department.delete()

class TestScoreValue(ApplyTest):
  def setUp(self):
    super(TestScoreValue, self).setUp()
    self.makeCSDept()
    cat = ScoreCategory(name='TheCat', shortform='TC', department=self.department)
    cat.save()
    self.category = cat
    val = ScoreValue(category=self.category, number=0, explanation='because',\
      department=self.department)
    val.save()
    self.value = val

  def testScoreValue(self):
    changeCap = bcap.grant('sv-change', self.value)
    changeCap.post({'explanation' : 'because i said so'})
    vals = ScoreValue.objects.filter(category=self.category, number=0,\
      explanation='because')
    self.assertEqual(len(vals), 0)
    vals = ScoreValue.objects.filter(category=self.category, number=0,\
      explanation='because i said so')
    self.assertEqual(len(vals), 1)
    vals.delete()

  def tearDown(self):
    self.department.delete()
    self.category.delete()

class TestApplicantPosition(ApplyTest):
  def setUp(self):
    super(TestApplicantPosition, self).setUp()
    self.makeCSDept()
  
  def testApplicantPosition(self):
    addCap = bcap.grant('ap-add', None)
    response = addCap.post({'department' : 'Computer Science', 'name' : 'Chairman',\
      'shortform' : 'CH', 'autoemail' : False})
    positions = ApplicantPosition.objects.filter(department=self.department,\
      name='Chairman', shortform='CH', autoemail=False)
    self.assertEquals(len(positions), 1)
    positions.delete()

  def tearDown(self):
    self.department.delete()

class TestArea(ApplyTest):
  def setUp(self):
    super(TestArea, self).setUp()
    self.makeCSDept()

  def testArea(self):
    addCap = bcap.grant('ar-add', None)
    response = addCap.post({\
      'name' : 'The Area',\
      'abbr' : 'TA', \
      'department' : 'Computer Science'\
    })
    self.assertTrue(response['success'] and response.has_key('delete'))
    areas = Area.objects.filter(name='The Area', abbr='TA', \
      department=self.department)
    self.assertEqual(len(areas), 1)

    delCap = response['delete']
    delCap.delete()
    areas = Area.objects.filter(name='The Area', abbr='TA', \
      department=self.department)
    self.assertEqual(len(areas), 0)

  def tearDown(self):
    self.department.delete()
    
