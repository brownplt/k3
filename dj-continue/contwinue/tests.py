import time, datetime

from django.test import TestCase

import contwinue.generate as generate
from contwinue.models import *
from contwinue.views import *

import belaylibs.dj_belay as bcap

# Note:  These tests rely on generate.py, which creates an initial department
# and fills it in with some data.

def has_keys(d, keys):
  return all([d.has_key(k) for k in keys])

class FakeHttp(object):
  def __init__(self, path, method):
    self.path_info = path
    self.method = method

class Generator(TestCase):
  def setUp(self):
    generate.generate(None)
    init = ContinueInit()
    init.process_request(None)

  def tearDown(self):
    Conference.get_by_shortname('SC').delete()

class TestBasic(Generator):
  def test_basic(self):
    conf = Conference.get_by_shortname('SC')
    
    req = FakeHttp('/SC/getBasic', 'GET')
    response = bcap.dataPostProcess(get_basic(req).content)
    
    self.assertEqual(response['info']['name'], 'Sample Conference')
    self.assertEqual(response['info']['shortname'], 'SC')
    self.assertEqual(response['adminContact'], 'joe@fake.com')

  def test_writer_basic(self):
    conf = Conference.get_by_shortname('SC')
    cap = bcap.grant('writer-basic', conf)

    response = cap.get()

    self.assertEqual(response['info']['name'], 'Sample Conference')
    self.assertEqual(response['info']['shortname'], 'SC')

    self.assertEqual(len(response['topics']), 10)
    # Only 1 because we filter for targetables
    self.assertEqual(len(response['decisions']), 1)
    # make_new makes 2
    self.assertEqual(len(response['components']), 4)

class TestAuthorLaunch(Generator):
  def setUp(self):
    super(TestAuthorLaunch, self).setUp()
    self.writer = User.objects.filter(username='writer')[0]
    self.paper = Paper.objects.filter(contact=self.writer)[0]

  def test_author_get(self):
    cap = bcap.grant('writer-paper-info', {'writer': self.writer, 'paper': self.paper})

    response = cap.get()

    self.assertEqual(response['title'], 'A synchronized real-time cache related to a virtual secure technology')
    self.assertEqual(response['components'][0]['value'], 'This is actually pretty short')
    self.assertEqual(response['author'], 'Joe Writer')
    self.assertEqual(response['pcpaper'], False)
    self.assertEqual(response['othercats'], True)
    self.assertTrue(type(response['target']['id']), int)
    self.assertEqual(len(response['topics']), 1)

  def test_extension(self):
    paperc = ComponentType.objects.filter(description='Paper')[0]

    newdeadline = int(time.time() + 24 * 3600 * 7)

    extension = DeadlineExtension(
      type=paperc,
      paper=self.paper,
      until=newdeadline,
      conference=self.writer.conference
    )
    extension.save()

    response = bcap.grant('paper-deadline-extensions', self.paper).get()

    self.assertEqual(response[0]['typeID'], paperc.id)
    self.assertEqual(response[0]['paperID'], self.paper.id)
    self.assertEqual(response[0]['untilStr'], convertTime(newdeadline))
    self.assertEqual(response[0]['until'], newdeadline)

  def test_set_title(self):
    response = bcap.grant('paper-set-title', self.paper).post({
      'title': 'Brand new work!'
    })
    afterwriter = User.objects.filter(username='writer')[0]
    afterpaper = Paper.objects.filter(contact=afterwriter)[0]

    self.assertEqual(response['title'], 'Brand new work!')
    self.assertEqual(afterpaper.title, 'Brand new work!')

  def test_set_author(self):
    response = bcap.grant('paper-set-author', self.paper).post({
      'author': 'Brand new author!'
    })
    afterwriter = User.objects.filter(username='writer')[0]
    afterpaper = Paper.objects.filter(contact=afterwriter)[0]

    self.assertEqual(response['author'], 'Brand new author!')
    self.assertEqual(afterpaper.author, 'Brand new author!')

  def test_set_author(self):
    response = bcap.grant('paper-set-pcpaper', self.paper).post({
      'pcpaper': 'yes'
    })
    afterwriter = User.objects.filter(username='writer')[0]
    afterpaper = Paper.objects.filter(contact=afterwriter)[0]

    self.assertEqual(response['pcpaper'], True)
    self.assertEqual(afterpaper.pc_paper, True)

  def test_set_topics(self):
    tnames = ['Distributed Systems', 'Computer Vision', 'Machine Learning']
    topics = [Topic.objects.filter(name=n)[0] for n in tnames]
    response = bcap.grant('paper-set-topics', self.paper).post({
      'topics': [t.id for t in topics]
    })

    afterpaper = Paper.objects.filter(contact=self.writer)[0]

    topicnames = [t.name for t in afterpaper.topic_set.all()]

    self.assertEqual(len(topicnames), 3)
    self.assertEqual(set([t.name for t in topics]), set(topicnames))

  def test_set_topics_to_none(self):
    response = bcap.grant('paper-set-topics', self.paper).post({
      'topics': []
    })

    afterpaper = Paper.objects.filter(contact=self.writer)[0]
    topicnames = [t.name for t in afterpaper.topic_set.all()]
    self.assertEqual(len(topicnames), 0)

  def test_set_target(self):
    target = DecisionValue.objects.filter(abbr='A')[0]
    response = bcap.grant('paper-set-target', self.paper).post({
      'targetID': target.id, 'othercats': 'no'
    })

    afterpaper = Paper.objects.filter(contact=self.writer)[0]
    self.assertEqual(afterpaper.target_id, target.id)
    self.assertEqual(afterpaper.other_cats, False)

    response = bcap.grant('paper-set-target', self.paper).post({
      'targetID': target.id, 'othercats': 'yes'
    })
    afterpaper = Paper.objects.filter(contact=self.writer)[0]
    self.assertEqual(afterpaper.target_id, target.id)
    self.assertEqual(afterpaper.other_cats, True)

  def test_update_components(self):
    pass
#    filedata = open('testfiles/testpdf.pdf', 'r').read()

#    acomp = ComponentType.objects.filter(abbr='A')[0]
#    pcomp = ComponentType.objects.filter(abbr='P')[0]

#    filesDict = {
#      'P': filedata
#    }
#    textDict = {
#      'A': 'This is the abstract'
#    }

#    handler = PaperUpdateComponentsHandler()
#    response = handler.post_files(self.paper, textDict, filesDict)

#    aftercomponent = Component.objects.filter(type=acomp, paper=self.paper)

#    component_path = os.path.join(settings.SAVEDFILES_DIR,
#                                  '%d-%d-component' % (self.paper.id, pcomp.id))

#    self.assertEqual(filedata, component_path.read())
#    self.assertEqual(aftercomponent.value, 'This is the abstract')

class TestAdminPage(Generator):
  def setUp(self):
    super(TestAdminPage, self).setUp()
    self.conference = Conference.get_by_shortname('SC')

  def test_get_admin(self):
    response = bcap.grant('get-admin', self.conference).get()
    self.assertTrue(has_keys(response,
      ['adminContact', 'dsCutoffHi', 'dsCutoffLo', 'dsConflictCut']))
    # TODO(matt): for now, adminContact is admin's email
    self.assertEqual(response['adminContact'], 'joe@fake.com')
    self.assertEqual(response['dsCutoffHi'], 7.0)
    self.assertEqual(response['dsCutoffLo'], 2.0)
    self.assertEqual(response['dsConflictCut'], 0.05)

  def test_get_all(self):
    def test_writer_user(writer, nstr):
      self.assertEqual(writer['username'], 'writer%s' % nstr)
      self.assertEqual(writer['fullname'], 'Joe Writer%s' % nstr)
      self.assertEqual(writer['email'], 'joe@writer%s.com' % nstr)
      self.assertEqual(len(writer['rolenames']), 1)
      self.assertEqual(writer['rolenames'][0], 'writer')
      self.assertEqual(writer['reviewCount'], 0)

    user_keys = ['username', 'fullname', 'email', 'rolenames', 'reviewCount']
    response = bcap.grant('get-all', self.conference).get()

    self.assertEqual(len(response), 11)
    self.assertTrue(all([has_keys(u, user_keys)\
      for u in response]))

    # Check admin user
    admin_users = filter(lambda u: 'admin' in u['rolenames'], response)
    self.assertEqual(len(admin_users), 1)
    admin_user = admin_users[0]
    self.assertEqual(admin_user['username'], 'admin')
    self.assertEqual(admin_user['fullname'], 'Joe Admin')
    self.assertEqual(admin_user['email'], 'joe@fake.com')
    self.assertEqual(len(admin_user['rolenames']), 2)
    self.assertTrue('reviewer' in admin_user['rolenames'])
    # TODO(matt): generate currently does not create reviews
    # must update this later when it does
    self.assertEqual(admin_user['reviewCount'], 0)

    # Check writer users
    writer_users = filter(lambda u: 'writer' in u['rolenames'], response)
    self.assertEqual(len(writer_users), 10)
    for wu in writer_users:
      if wu['username'] == 'writer':
        nstr = ''
      else:
        nstr = wu['username'][6:]
      test_writer_user(wu, nstr)

  def test_topic_add(self):
    self.assertEqual(len(Topic.objects.all()), 10)
    add_cap = bcap.grant('add-topic', self.conference)
    response = add_cap.post({'name' : 'New Topic'})
    self.assertTrue(response.has_key('name'))
    self.assertEqual(response['name'], 'New Topic')
    self.assertEqual(len(Topic.objects.all()), 11)
    add_cap.post({'name' : 'New Topic'})
    self.assertEqual(len(Topic.objects.all()), 11)

  def test_topic_delete(self):
    all_topics = Topic.objects.all()
    t = all_topics[0]
    t_name = t.name
    num_before = len(all_topics)

    bcap.grant('delete-topic', t).delete()
    self.assertEqual(num_before - 1, len(Topic.objects.all()))
    self.assertEqual(0, len(Topic.objects.filter(name=t_name)))

  def test_decision_value_add(self):
    num_values = len(DecisionValue.objects.all())
    add_cap = bcap.grant('add-decision-value', self.conference)
    self.assertEqual(0, len(DecisionValue.objects.filter(
      abbr='X',
      description='A New Decision Value',
      targetable=True)))
    response = add_cap.post({
      'abbr' : 'X',
      'description' : 'A New Decision Value',
      'targetable' : True
    })
    self.assertTrue(has_keys(response, ['abbr', 'targetable', 'description']))
    self.assertEqual(num_values + 1, len(DecisionValue.objects.all()))
    self.assertEqual(1, len(DecisionValue.objects.filter(
      abbr='X',
      description='A New Decision Value',
      targetable=True)))
    # Repeat to test only creating 1
    response = add_cap.post({
      'abbr' : 'X',
      'description' : 'A New Decision Value',
      'targetable' : True
    })
    self.assertTrue(has_keys(response, ['abbr', 'targetable', 'description']))
    self.assertEqual(num_values + 1, len(DecisionValue.objects.all()))
    self.assertEqual(1, len(DecisionValue.objects.filter(
      abbr='X',
      description='A New Decision Value',
      targetable=True)))

  def test_decision_value_delete(self):
    all_values = DecisionValue.objects.all()
    dv = all_values[0]
    abbr = dv.abbr
    description = dv.description
    targetable = dv.targetable
    num_before = len(all_values)

    bcap.grant('delete-decision-value', dv).delete()

    self.assertEqual(num_before - 1, len(DecisionValue.objects.all()))
    self.assertEqual(0, len(DecisionValue.objects.filter(abbr=abbr,\
      description=description, targetable=targetable, \
      conference=self.conference)))
