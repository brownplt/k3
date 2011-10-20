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

class TestNewAccount(ApplyTest):
  def setUp(self):
    super(TestNewAccount, self).setUp()
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
    reviewer_info = create_cap.post({})
    info = AuthInfo.objects.filter(email="reviewer@fake")
    self.assertEqual(len(info), 1)
    revs = Reviewer.objects.filter(auth=info[0])
    self.assertEqual(revs[0].committee, False)

    self.assertTrue(isinstance(reviewer_info['private_data'], bcap.Capability))
    self.assertEqual(reviewer_info['public_data'], 'Reviewer account for Fake Reviewer')

    # The capability to create shouldn't work twice
    try:
      create_cap.post({})
      self.assertTrue(False)
    except:
      self.assertTrue(True)

def TestAdminAccount(ApplyTest):
  def setUp(self):
    super(TestAdminAccount, self).setUp()
    self.makeCSDept()

  def testAdminAccount(self):
    unverified_user = UnverifiedUser( \
      role='admin',
      name='Default Admin',
      email='default@fake',
      department=self.department)
    unverified_user.save()
    create_cap = bcap.grant('add-admin', unverified_user)

    admin_info = create_cap.post({})
    info = AuthInfo.objects.filter(email='default@fake')

    self.assertEqual(len(info), 1)
    self.assertEqual(info[0].email, 'default@fake')
    self.assertEqual(info[0].role, 'admin')

    self.assertTrue(isinstance(admin_info['private_data'], bcap.Capability))

class TestScoreCategory(ApplyTest):
  def setUp(self):
    super(TestScoreCategory, self).setUp()
    self.makeCSDept()

  def testScoreCategory(self):
    args = {\
      'name' : 'Category Uno',\
      'shortform' : 'CU',\
    }

    addCap = bcap.grant('scorecategory-add', self.department)
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
    changeCap = bcap.grant('scorevalue-change', self.value)
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
    addCap = bcap.grant('applicantposition-add', self.department)
    response = addCap.post({'name' : 'Chairman', 'shortform' : 'CH',\
      'autoemail' : False})
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
    addCap = bcap.grant('area-add', self.department)
    response = addCap.post({\
      'name' : 'The Area',\
      'abbr' : 'TA', \
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
    
class TestUnverifiedUser(ApplyTest):
  def setUp(self):
    super(TestUnverifiedUser, self).setUp()
    self.makeCSDept()

  def testUnverifiedUser(self):
    rev1data = {\
      'email' : 'blah@blah.com',\
      'role' : 'reviewer',\
      'name' : 'Matt'\
    }
    rev2data = {\
      'email' : 'blah2@blah.com',\
      'role' : 'applicant',\
      'name' : 'Some Guy'\
    }

    addRevCap = bcap.grant('unverifieduser-addrev', self.department)
    response = addRevCap.post(rev1data)
    self.assertTrue(response['success'] and response.has_key('delete'))
    users = UnverifiedUser.objects.filter(name='Matt', email='blah@blah.com',\
      role='reviewer', department=self.department)
    self.assertEqual(len(users), 1)

    delCap = response['delete']
    delCap.delete()
    users = UnverifiedUser.objects.filter(name='Matt', email='blah@blah.com',\
      role='reviewer', department=self.department)
    self.assertEqual(len(users), 0)

    reviewerResponse = addRevCap.post(rev1data)
    applicantResponse = addRevCap.post(rev2data)
    getPendingCap = bcap.grant('unverifieduser-getpending', self.department)
    pendingResponse = getPendingCap.get()
    self.assertEqual(len(pendingResponse), 1)
    rev1info = pendingResponse[0]
    for (k, v) in rev1data.iteritems():
      self.assertTrue(rev1info.has_key(k))
      self.assertEqual(rev1info[k], v)
    
    reviewerResponse['delete'].delete()
    applicantResponse['delete'].delete()
  
  def tearDown(self):
    self.department.delete()

class TestGetReviewers(ApplyTest):
  def setUp(self):
    super(TestGetReviewers, self).setUp()
    self.makeCSDept()
    a = AuthInfo(email='blah@blah.com', name='Matt', role='admin', \
      department=self.department)
    a.save()
    r = Reviewer(auth=a, committee=True, department=self.department)
    r.save()
    self.auth = a
    self.reviewer = r

  def testGetReviewers(self):
    getReviewersCap = bcap.grant('get-reviewers', self.department)
    reviewers = getReviewersCap.get()
    self.assertEqual(len(reviewers), 1)
    r = reviewers[0]
    self.assertEqual(r['email'], self.auth.email)
    self.assertEqual(r['name'], self.auth.name)
    self.assertEqual(r['role'], self.auth.role)
    self.assertEqual(r['committee'], self.reviewer.committee)

    self.reviewer.delete()
    reviewers = getReviewersCap.get()
    self.assertEqual(len(reviewers), 0)

  def tearDown(self):
    self.department.delete()

class TestChangeContacts(ApplyTest):
  def setUp(self):
    super(TestChangeContacts, self).setUp()
    self.makeCSDept()

  def testChangeContacts(self):
    olddepts = Department.objects.filter(contactName='Donald Knuth',\
      contactEmail='test@example.com', techEmail='tech@example.com')
    self.assertEqual(len(olddepts), 1)

    changeContactsCap = bcap.grant('change-contacts', self.department)
    response = changeContactsCap.post({\
      'contactName' : 'some dude',\
      'contactEmail' : 'some@dude.com',\
      'techEmail' : 'somedude@tech.com'\
    })

    self.assertTrue(response['success'])
    olddepts = Department.objects.filter(contactName='Donald Knuth',\
      contactEmail='test@example.com', techEmail='tech@example.com')
    self.assertEqual(len(olddepts), 0)
    newdepts = Department.objects.filter(contactName='some dude',\
      contactEmail='some@dude.com', techEmail='somedude@tech.com')
    self.assertEqual(len(newdepts), 1)

  def tearDown(self):
    self.department.delete()
