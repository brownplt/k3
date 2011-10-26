import unittest
from apply.models import *
from apply.views import *
from datetime import date

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
    unverified_user = UnverifiedUser( \
      role='reviewer',
      name='Fake Reviewer',
      email='reviewer@fake',
      department=self.department)
    unverified_user.save()
    create_cap = bcap.grant('add-reviewer', unverified_user)

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
      'minval' : 0,\
      'maxval' : 10\
    }

    addCap = bcap.grant('scorecategory-add', self.department)
    response = addCap.post(args)
    self.assertTrue(response.has_key('success'))
    self.assertTrue(response['success'])
    for k in args.keys():
      self.assertTrue(response.has_key(k))
      self.assertEqual(response[k], args[k])

    scs = ScoreCategory.objects.filter(name=args['name'])
    self.assertEqual(len(scs), 1)
    sc = scs[0]
    changeCap = bcap.grant('scorecategory-change', sc)
    new_args = {'name' : 'changed name', 'shortform' : 'cn'}
    response = changeCap.post(new_args)
    self.assertTrue(response.has_key('success'))
    self.assertTrue(response['success'])
    for k in new_args.keys():
      self.assertTrue(response.has_key(k), 'response missing key = ' + k)
      self.assertEqual(response[k], new_args[k])
    old_scs = ScoreCategory.objects.filter(name=args['name'],\
      shortform=args['shortform'])
    self.assertEqual(len(old_scs), 0)
    new_scs = ScoreCategory.objects.filter(name=new_args['name'],\
      shortform=new_args['shortform'])
    self.assertEqual(len(new_scs), 1)
    
    sc = new_scs[0]
    delCap = bcap.grant('scorecategory-delete', sc)
    sc.delete()
    new_scs = ScoreCategory.objects.filter(name=new_args['name'],\
      shortform=new_args['shortform'])

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
    change_resp = changeCap.post({'explanation' : 'because i said so'})
    self.assertTrue(change_resp.has_key('success'))
    self.assertTrue(change_resp['success'])
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

    addRevCap = bcap.grant('unverifieduser-addrev', self.department)
    response = addRevCap.post(rev1data)
    self.assertTrue(response.has_key('success'))
    self.assertTrue(response['success'])
    for (k, v) in rev1data.iteritems():
      self.assertTrue(response.has_key(k))
      self.assertEqual(response[k], v)
    uus = UnverifiedUser.objects.filter(name=rev1data['name'],\
      role=rev1data['role'], email=rev1data['email'])
    self.assertEqual(len(uus), 1)

    getPenCap = bcap.grant('unverifieduser-getpending', self.department)
    response = getPenCap.get()
    self.assertEqual(len(response), 1)
    p = response[0]
    self.assertTrue(p.has_key('del'))
    for (k, v) in rev1data.iteritems():
      self.assertTrue(p.has_key(k))
      self.assertEqual(p[k], v)

    delCap = p['del']
    delCap.delete()
    uus = UnverifiedUser.objects.filter(name=rev1data['name'],\
      role=rev1data['role'], email=rev1data['email'])
    self.assertEqual(len(uus), 0)
  
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

class TestFindRefs(ApplyTest):
  def setUp(self):
    super(TestFindRefs, self).setUp()
    self.makeCSDept()
    self.auth = AuthInfo(email='foo@foo.com', name='foo', role='applicant',\
      department=self.department)
    self.auth.save()
    self.position = ApplicantPosition(department=self.department, name='thepos',\
      shortform='tp', autoemail='auto@email.com')
    self.position.save()
    self.applicant = Applicant(auth=self.auth, firstname='foo', lastname='foo',\
      country='usa', department=self.department, position=self.position)
    self.applicant.save()
    self.reference = Reference(code=0, applicant=self.applicant, submitted=0,\
      filesize=0, name='bar', email='bar@bar.com', department=self.department,\
      lastRequested=0)
    self.reference.save()

  def testFindRefs(self):
    findRefsCap = bcap.grant('find-refs', self.department)
    response = findRefsCap.post({'email' : 'bar@bar.com'})
    self.assertEqual(len(response), 1)
    ref = response[0]
    self.assertEqual(ref['appname'],\
      self.applicant.firstname + ' ' + self.applicant.lastname)
    self.assertEqual(ref['appemail'], self.applicant.auth.email)

  def tearDown(self):
    self.department.delete()

class TestGetBasic(ApplyTest):
  def setUp(self):
    super(TestGetBasic, self).setUp()
    self.makeCSDept()
    self.area = Area(name='area', abbr='ar', department=self.department)
    self.area.save()
    auth = AuthInfo(email='foo@foo.com', name='foo', role='applicant',\
      department=self.department)
    auth.save()
    self.position = ApplicantPosition(department=self.department, name='thepos',\
      shortform='tp', autoemail=True)
    self.position.save()
    self.component = ComponentType(type='type', value='value', lastSubmitted=0,\
      department=self.department, date=date.today())
    self.component.save()
    self.applicant = Applicant(auth=auth, firstname='foo', lastname='foo',\
      country='usa', department=self.department, position=self.position)
    self.applicant.save()
    sc = ScoreCategory(name='scorecategory', shortform='sc', department=self.department)
    sc.save()
    sv = ScoreValue(category=sc, number=0, explanation='exp', department=self.department)
    sv.save()
    applicant = Applicant(auth=auth, firstname='foo', lastname='foo',\
      country='usa', department=self.department, position=self.position)
    applicant.save()
    reviewer = Reviewer(auth=auth, committee=False, department=self.department)
    reviewer.save()
    review = Review(applicant=applicant, reviewer=reviewer, comments='comments',\
      draft=False, department=self.department)
    review.save()
    self.score = Score(value=sv, review=review, department=self.department)
    self.score.save()
    self.degree = Degree(name='degree', shortform='dg', department=self.department)
    self.degree.save()

  def testGetBasic(self):
    getBasicCap = bcap.grant('get-basic', self.department)
    response = getBasicCap.get()

    self.assertTrue(response.has_key('info'))
    i = response['info']
    self.assertEqual(i['name'], self.department.name)
    self.assertEqual(i['shortname'], self.department.shortname)
    self.assertEqual(i['lastChange'], self.department.lastChange)
    self.assertEqual(i['brandColor'], self.department.brandColor)
    self.assertEqual(i['contactName'], self.department.contactName)
    self.assertEqual(i['contactEmail'], self.department.contactEmail)
    self.assertEqual(i['techEmail'], self.department.techEmail)

    self.assertTrue(response.has_key('countries'))
    self.assertEqual(len(response['countries']), 1)
    self.assertEqual(response['countries'][0], 'usa')

    self.assertTrue(response.has_key('areas'))
    self.assertEqual(len(response['areas']), 1)
    a = response['areas'][0]
    self.assertEqual(a['name'], 'area')
    self.assertEqual(a['abbr'], 'ar')

    self.assertTrue(response.has_key('positions'))
    self.assertEqual(len(response['positions']), 1)
    p = response['positions'][0]
    self.assertEqual(p['name'], 'thepos')
    self.assertEqual(p['shortform'], 'tp')
    self.assertEqual(p['autoemail'], True)

    self.assertTrue(response.has_key('components'))
    self.assertEqual(len(response['components']), 1)
    c = response['components'][0]
    self.assertEqual(c['type'], 'type')
    self.assertEqual(c['value'], 'value')
    self.assertEqual(c['lastSubmitted'], 0)
    self.assertEqual(c['date'], str(date.today()))

    self.assertTrue(response.has_key('scores'))
    s = response['scores'][0]
    self.assertEqual(len(response['scores']), 1)
    self.assertTrue(s.has_key('values'))
    svals = s['values']
    self.assertEqual(len(svals), 1)
    self.assertEqual(svals[0]['explanation'], 'exp')
    self.assertEqual(svals[0]['number'], 0)
    self.assertTrue(svals[0].has_key('change'))
    self.assertTrue(s.has_key('del'))
    self.assertTrue(s.has_key('name'))
    self.assertEquals(s['name'], 'scorecategory')
    self.assertTrue(s.has_key('change'))
    self.assertTrue(s.has_key('shortform'))
    self.assertEquals(s['shortform'], 'sc')

    self.assertTrue(response.has_key('degrees'))
    self.assertEqual(len(response['degrees']), 1)
    d = response['degrees'][0]
    self.assertEqual(d['name'], 'degree')
    self.assertEqual(d['shortform'], 'dg')

  def testSetBasic(self):
    setBasicCap = bcap.grant('set-basic', self.department)
    newinfo = {\
      'name' : 'updated name',\
      'shortname' : 'un',\
      'lastChange' : 1,\
      'brandColor' : 'updated color',\
      'contactName' : 'updated contactName',\
      'contactEmail' : 'updated@email.com',\
      'techEmail' : 'updated@tech.com'\
    }
    response = setBasicCap.post(newinfo)
    self.assertTrue(response.has_key('success'))
    self.assertTrue(response['success'])

    old = Department.objects.filter(name='Computer Science', shortname='CS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    self.assertEqual(len(old), 0)
    new = Department.objects.filter(name='updated name', shortname='un',\
      lastChange=1, brandColor='updated color', contactName='updated contactName',\
      contactEmail='updated@email.com', techEmail='updated@tech.com')
    self.assertEqual(len(new), 1)
    self.department = new[0]

  def tearDown(self):
    self.department.delete()

class TestGetCSV(ApplyTest):
  pass

class TestAdminLaunch(ApplyTest):
  def setUp(self):
    super(TestAdminLaunch, self).setUp()
    self.makeCSDept()
    self.area = Area(name='area', abbr='ar', department=self.department)
    self.area.save()
    auth = AuthInfo(email='foo@foo.com', name='foo', role='applicant',\
      department=self.department)
    auth.save()
    self.position = ApplicantPosition(department=self.department, name='thepos',\
      shortform='tp', autoemail=True)
    self.position.save()
    self.component = ComponentType(type='type', value='value', lastSubmitted=0,\
      department=self.department, date=date.today())
    self.component.save()
    self.applicant = Applicant(auth=auth, firstname='foo', lastname='foo',\
      country='usa', department=self.department, position=self.position)
    self.applicant.save()
    sc = ScoreCategory(name='scorecategory', shortform='sc', department=self.department)
    sc.save()
    sv = ScoreValue(category=sc, number=0, explanation='exp', department=self.department)
    sv.save()
    applicant = Applicant(auth=auth, firstname='foo', lastname='foo',\
      country='usa', department=self.department, position=self.position)
    applicant.save()
    reviewer = Reviewer(auth=auth, committee=False, department=self.department)
    reviewer.save()
    review = Review(applicant=applicant, reviewer=reviewer, comments='comments',\
      draft=False, department=self.department)
    review.save()
    self.score = Score(value=sv, review=review, department=self.department)
    self.score.save()
    self.degree = Degree(name='degree', shortform='dg', department=self.department)
    self.degree.save()

    self.auth = auth

  def testAdminLaunch(self):
    adminLaunchCap = bcap.grant('launch-admin', self.auth)
    response = adminLaunchCap.get()

    self.assertTrue(response.has_key('getReviewers'))
    self.assertTrue(response.has_key('UnverifiedUserAddRev'))
    self.assertTrue(response.has_key('UnverifiedUserGetPending'))
    self.assertTrue(response.has_key('ScoreCategoryAdd'))
    self.assertTrue(response.has_key('ApplicantPositionAdd'))
    self.assertTrue(response.has_key('AreaAdd'))
    self.assertTrue(response.has_key('getBasic'))
    self.assertTrue(response.has_key('setBasic'))
    self.assertTrue(response.has_key('getCSV'))

  def tearDown(self):
    self.department.delete()
