import time, datetime, os

import json

from django.core import mail
from django.test import TestCase

import contwinue.generate as generate
from contwinue.models import *
from contwinue.views import *
import contwinue.email_strings as strings

import belaylibs.dj_belay as bcap

# Note:  These tests rely on generate.py, which creates an initial department
# and fills it in with some data.

def make_author(full_name, email, conference):
  account = Account(key=str(uuid.uuid4()))
  account.save()
  user = User(
    full_name=full_name,
    email=email,
    conference=conference,
    account=account
  )
  user.save()
  return user
  

def has_keys(d, keys):
  return all([d.has_key(k) for k in keys])

class FakeHttp(object):
  def __init__(self, path, method):
    self.path_info = path
    self.method = method

class Generator(TestCase):
  def setUp(self):
    generate.generate()
    init = ContinueInit()
    init.process_request(None)
    self.conference = Conference.get_by_shortname('SC')

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
    self.conference = self.writer.conference

  def test_make_user(self):
    email = 'harry@hogwarts.edu'
    name = 'Harry Potter'
    uu = UnverifiedUser(
      email=email,
      name=name,
      conference=self.conference
    )
    uu.save()

    self.paper.unverified_authors.add(uu)
    self.paper.save()

    (account, user) = make_user(uu)

    newuser = get_one(User.objects.filter(email=user.email))

    self.assertEqual(user.full_name, name)
    self.assertEqual(user.email, email)
    self.assertEqual(user.conference, self.conference)

    self.assertFalse(self.paper in uu.paper_set.all())
    self.assertTrue(self.paper in newuser.papers.all())

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

    self.assertEqual(response['authors'][0]['email'], self.writer.email)
    self.assertEqual(len(response['authors']), 1)

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

  def test_set_pcpaper(self):
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
    f = open('testdata/testpdf.pdf', 'r')

    acomp = ComponentType.objects.filter(abbr='A')[0]
    pcomp = ComponentType.objects.filter(abbr='P')[0]

    filesDict = {
      'P': f
    }
    textDict = {
      'A': 'This is the abstract'
    }

    handler = PaperUpdateComponentsHandler()
    response = handler.post_files(self.paper, textDict, filesDict)

    self.assertEqual(bcap.dataPostProcess(response.content), True)

    aftercomponent = get_one(Component.objects.filter(type=acomp, paper=self.paper))
    afterpaper = get_one(Component.objects.filter(type=pcomp, paper=self.paper))

    component_path = os.path.join(settings.SAVEDFILES_DIR,
                                  '%d-%d-component' % (self.paper.id, pcomp.id))

    filedata = open('testdata/testpdf.pdf', 'r').read()
    self.assertEqual(filedata, file(component_path).read())
    self.assertEqual(afterpaper.value, 'testdata/testpdf.pdf')
    # TODO(joe): Why charset=binary here?  Should it be utf-8?
    self.assertEqual(afterpaper.mimetype, 'application/pdf; charset=binary')

    self.assertEqual(aftercomponent.value, 'This is the abstract')
    self.assertEqual(aftercomponent.mimetype, 'text/plain')

  def test_update_non_pdf(self):
    f = open('testdata/not-a-pdf.txt', 'r')

    pcomp = ComponentType.objects.filter(abbr='P')[0]
    filesDict = { 'P': f }

    handler = PaperUpdateComponentsHandler()
    response = handler.post_files(self.paper, {}, filesDict)

    self.assertEqual(bcap.dataPostProcess(response.content),
      {'error': 'The file you uploaded was not a PDF document.'})

  def test_add_author(self):
    settings.DEBUG=False
    author = get_one(User.objects.filter(email='joe@writer.com'))
    paper = get_one(Paper.objects.filter(contact=author))

    addauthor = bcap.grant('paper-add-author', {'paper': paper, 'user': author})
    response = addauthor.post({'email': 'sk@cs.fake', 'name': 'Shriram Krishnamurthi'})

    self.assertEqual(response, {'name': 'Shriram Krishnamurthi',
                                'email': 'sk@cs.fake'})

    uu = get_one(UnverifiedUser.objects.filter(email='sk@cs.fake'))
    self.assertTrue(not (uu is None))
    self.assertEqual(uu.name, 'Shriram Krishnamurthi')

    self.assertTrue(uu in paper.unverified_authors.all())

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(
      mail.outbox[0].subject,
      strings.add_author_subject % {
        'confname': author.conference.name,
        'paper_title': paper.title
      }
    )

    granted_cap = get_one(Grant.objects.filter(
      internal_path='launch-attach-to-paper',
      db_data=bcap.dbPreProcess({'newuser': True, 'unverified': uu, 'paper': paper})
    ))
    
    self.assertTrue(granted_cap is not None)

    # Make sure the cap id shows up in the email
    self.assertTrue(mail.outbox[0].body.find(granted_cap.cap_id) != -1)
    settings.DEBUG=True

  def test_add_author_existing(self):
    settings.DEBUG=False
    author = get_one(User.objects.filter(email='joe@writer.com'))
    paper = get_one(Paper.objects.filter(contact=author))

    user_email = 'joe@writer2.com'
    addauthor = bcap.grant('paper-add-author', {'paper': paper, 'user': author})
    response = addauthor.post({'email': user_email, 'name': 'Joe the Writer'})
    existing_user = get_one(User.objects.filter(email=user_email, conference=paper.conference))

    self.assertEqual(response, {'email': user_email, 'name':existing_user.full_name})
    uu = get_one(UnverifiedUser.objects.filter(email=user_email))
    self.assertTrue(uu is None)

    self.assertTrue(existing_user in paper.authors.all())

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(
      mail.outbox[0].subject,
      strings.add_author_subject % {
        'confname': author.conference.name,
        'paper_title': paper.title
      }
    )

    granted_cap = get_one(Grant.objects.filter(
      internal_path='launch-paper',
      db_data=bcap.dbPreProcess({'user': existing_user, 'paper': paper})
    ))
    
    self.assertTrue(granted_cap is not None)

    # Make sure the cap id shows up in the email
    self.assertTrue(mail.outbox[0].body.find(granted_cap.cap_id) != -1)
    settings.DEBUG=True

  def test_launch_new_paper(self):
    uu = UnverifiedUser(
      name='Hermione Granger',
      email='hermione@hogwarts.edu',
      conference=self.writer.conference,
      roletext='user'
    )
    uu.save()

    launch_new_cap = bcap.grant('launch-new-paper', {
      'create': True,
      'unverified': uu
    })

    response = launch_new_cap.get()

    newuser = get_one(User.objects.filter(email='hermione@hogwarts.edu'))
    newpaper = get_one(Paper.objects.filter(contact=newuser))

    self.assertTrue(response['newUser'])
    self.assertEqual(newuser.full_name, uu.name)
    self.assertEqual(newuser.email, uu.email)
    self.assertEqual(newuser.conference, uu.conference)
    self.assertEqual(newpaper.contact, newuser)
    self.assertEqual(len(newpaper.authors.all()), 1)
    self.assertEqual(len(response['papers']), 1)
    self.assertEqual(response['papers'][0]['id'], newpaper.id)
    self.assertEqual(len(newpaper.unverified_authors.all()), 0)
    self.assertEqual(len(newpaper.authors.all()), 1)

    the_grant = get_one(Grant.objects.filter(cap_id=bcap.cap_id_from_url(launch_new_cap.serialize())))
    self.assertEqual(
      the_grant.db_data,
      bcap.dbPreProcess({'create': False, 'user': newuser, 'paper': newpaper})
    )

    # Now, when you invoke again immediately, the *only* difference should be
    # the newUser flag
    response2 = launch_new_cap.get()
    self.assertFalse(response2['newUser'])

    del response['newUser']
    del response2['newUser']
    
    self.assertEqual(bcap.dataPreProcess(response), bcap.dataPreProcess(response2))


  # If we try to launch with an unverified user who already has a user with
  # that email verified, we simply launch with that account
  def test_launch_new_paper_existing_uu(self):
    user = make_author(
      full_name='Ron Weasley',
      email='ronald@hogwarts.edu',
      conference=self.conference
    )

    uu = UnverifiedUser(
      name='Ron Different',
      email='ron@hogwarts.edu',
      roletext='user',
      conference=self.conference
    )
    uu.save()

    users_before = User.objects.all()

    launch_new_cap = bcap.grant('launch-new-paper', {
      'create': True,
      'unverified': uu
    })
    response = launch_new_cap.get()

    users_after = User.objects.all()

    self.assertEqual(len(response['papers']), 1)
    self.assertEqual(set(users_before), set(users_after))
    self.assertEqual(response['mainTitle'], u'')

  def test_launch_attach_to_paper(self):
    uu = UnverifiedUser(
      name='Severus Snape',
      email='jerk@hogwarts.edu',
      conference=self.writer.conference,
      roletext='user'
    )
    uu.save()

    paper = Paper(
      contact=self.writer,
      title=u'Potions and Stuff',
      conference=self.conference,
      target=self.conference.default_target
    )
    paper.save()
    paper.authors.add(self.writer)
    paper.unverified_authors.add(uu)
    self.assertTrue(uu in paper.unverified_authors.all())

    launch_new_cap = bcap.grant('launch-attach-to-paper', {
      'newuser': True,
      'unverified': uu,
      'paper': paper
    })

    response = launch_new_cap.get()

    self.assertEqual(response['mainTitle'], paper.title)
    self.assertTrue(response['newUser'])

    newuser = get_one(User.objects.filter(email='jerk@hogwarts.edu'))
    newuu = get_one(UnverifiedUser.objects.filter(email='jerk@hogwarts.edu'))
    newpaper = get_one(Paper.objects.filter(title=u'Potions and Stuff'))

    self.assertFalse(newuu in newpaper.unverified_authors.all())
    self.assertFalse(newpaper in newuu.paper_set.all())
    self.assertTrue(newpaper in newuser.papers.all())
    self.assertTrue(newuser in newpaper.authors.all())
    self.assertEqual(len(newuser.papers.all()), 1)

  def test_launch_attach_to_paper_existing(self):
    user = make_author(
      full_name='Luna Lovegood',
      email='luna@hogwarts.edu',
      conference=self.conference
    )

    uu = UnverifiedUser(
      name='Luna Lovebad',
      email='luna@hogwarts.edu',
      roletext='user',
      conference=self.conference
    )
    uu.save()

    paper = Paper(
      contact=self.writer,
      title=u'Multicore Polyjuice Potion',
      conference=self.conference,
      target=self.conference.default_target
    )
    paper.save()

    authors_before = list(paper.authors.all())
    
    launch_cap = bcap.grant('launch-attach-to-paper', {
      'newuser': True,
      'unverified': uu,
      'paper': paper
    })

    response = launch_cap.get()

    newuser = get_one(User.objects.filter(email='luna@hogwarts.edu'))
    newpaper = get_one(Paper.objects.filter(title=u'Multicore Polyjuice Potion'))

    authors_after = newpaper.authors.all()
    papers_after = newuser.papers.all()

    self.assertEqual(len(authors_before), 0)
    self.assertEqual(len(authors_after), 1)
    self.assertEqual(len(papers_after), 1)

    self.assertEqual(user, newuser)
    self.assertEqual(authors_after[0], newuser)

    the_grant = get_one(Grant.objects.filter(cap_id=bcap.cap_id_from_url(launch_cap.serialize())))
    self.assertEqual(
      json.loads(the_grant.db_data),
      json.loads(bcap.dbPreProcess({
        'newuser': False,
        'user': newuser,
        'paper': paper
      }))
    )

class TestUpdateAuthorName(Generator):
  def test_change_name(self):
    user = make_author(
      full_name=u'Albus Dumbledore',
      email='dominator@hogwarts.edu',
      conference=self.conference
    )

    change_name = bcap.grant('user-update-name', user)
    response = change_name.post({'name': u'New Dumbledore'})

    self.assertEqual(response, {'name': u'New Dumbledore'})

    userafter = get_one(User.objects.filter(email='dominator@hogwarts.edu'))
    self.assertEqual(userafter.full_name, u'New Dumbledore')

class TestRemoveAuthor(Generator):
  def test_remove_existing_user(self):
    user = make_author(
      full_name=u'Nevill Longbottom',
      email='neville@hogwarts.edu',
      conference=self.conference
    )
    user2 = make_author(
      full_name='Draco Malfoy',
      email='draco@hogwarts.edu',
      conference=self.conference
    )

    paper = Paper(
      contact=user,
      title=u'Defense Against the Dark Farts',
      target=self.conference.default_target,
      conference=self.conference
    )
    paper.save()
    paper.authors.add(user, user2)

    remove_author = bcap.grant('paper-remove-author', {
      'paper': paper,
      'user': user2
    })
    response = remove_author.post({})

    self.assertEqual({'success': True}, response)

    self.assertTrue(user in paper.authors.all())
    self.assertTrue(user2 not in paper.authors.all())

  def test_remove_author_unverified(self):
    uhagrid = UnverifiedUser(
      name='Rubeus Hagrid',
      email='facilities@hogwarts',
      conference=self.conference
    )
    uhagrid.save()
    minerva = make_author(
      full_name='Minerva McGonnagal',
      email='mcg@hogwarts.edu',
      conference=self.conference
    )

    paper = Paper(
      contact=minerva,
      title=u'Transmuting Groundskeepers to Professors',
      target=self.conference.default_target,
      conference=self.conference
    )
    paper.save()
    paper.authors.add(minerva)
    paper.unverified_authors.add(uhagrid)

    remove_cap = bcap.grant('paper-remove-author', {
      'unverified': uhagrid,
      'paper': paper
    })

    response = remove_cap.post({})

    self.assertEqual({'success': True}, response)

    self.assertTrue(uhagrid not in paper.unverified_authors.all())
    self.assertTrue(minerva in paper.authors.all())

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

  def test_add_review_component_type(self):
    num_types = len(ReviewComponentType.objects.all())
    add_cap = bcap.grant('add-review-component-type', self.conference)
    description = 'A new review component type'

    response = add_cap.post({'description' : description, 'pcOnly' : False})

    self.assertTrue(has_keys(response, ['description', 'pcOnly']))
    self.assertEquals(response['description'], description)
    self.assertEquals(response['pcOnly'], False)
    self.assertEquals(num_types + 1, len(ReviewComponentType.objects.all()))
    self.assertEquals(1, len(ReviewComponentType.objects.filter(\
      description=description, pc_only=False)))

    add_cap.post({'description' : description, 'pcOnly' : False})
    self.assertEquals(response['description'], description)
    self.assertEquals(response['pcOnly'], False)
    self.assertEquals(num_types + 1, len(ReviewComponentType.objects.all()))
    self.assertEquals(1, len(ReviewComponentType.objects.filter(\
      description=description, pc_only=False)))

  def test_add_component_type(self):
    num_types = len(ComponentType.objects.all())
    add_cap = bcap.grant('add-component-type', self.conference)
    abbr = '<'
    description = 'A new component type'
    format_ = 'Any'
    deadline = int(time.time())
    grace_hours = 10
    size_limit = 1000000000000
    response = add_cap.post({
      'abbr' : abbr,
      'description' : description,
      'format' : format_,
      'deadline' : deadline,
      'mandatory' : False,
      'gracehours' : grace_hours,
      'sizelimit' : size_limit
    })
    self.assertTrue(has_keys(response, ['abbr', 'description', 'format', \
      'deadline', 'mandatory', 'gracehours','sizelimit']))
    self.assertEquals(num_types + 1, len(ComponentType.objects.all()))
    self.assertEquals(1, len(ComponentType.objects.filter(abbr=abbr,\
      description=description, fmt=format_, deadline=deadline, mandatory=False,\
      grace_hours=grace_hours, size_limit=size_limit)))
    response = add_cap.post({
      'abbr' : abbr,
      'description' : description,
      'format' : format_,
      'deadline' : deadline,
      'mandatory' : False,
      'gracehours' : grace_hours,
      'sizelimit' : size_limit
    })
    self.assertTrue(has_keys(response, ['abbr', 'description', 'format', \
      'deadline', 'mandatory', 'gracehours','sizelimit']))
    self.assertEquals(num_types + 1, len(ComponentType.objects.all()))
    self.assertEquals(1, len(ComponentType.objects.filter(abbr=abbr,\
      description=description, fmt=format_, deadline=deadline, mandatory=False,\
      grace_hours=grace_hours, size_limit=size_limit)))

  def test_delete_component_type(self):
    num_types = len(ComponentType.objects.all())
    ct = ComponentType.objects.all()[0]
    abbr = ct.abbr

    bcap.grant('delete-component-type', ct).delete()

    self.assertEqual(num_types - 1, len(ComponentType.objects.all()))
    self.assertEqual(0, len(ComponentType.objects.filter(abbr=abbr,\
      conference=self.conference)))

  def test_change_component_type(self):
    def changed_fmt(prior_fmt):
      fmts = [f[0] for f in ComponentType.formats]
      return fmts[(1 + fmts.index(prior_fmt)) % len(fmts)]

    ct = ComponentType.objects.all()[0]
    abbr = ct.abbr
    description = ct.description
    fmt = ct.fmt
    deadline = ct.deadline
    mandatory = ct.mandatory
    grace_hours = ct.grace_hours
    size_limit = ct.size_limit

    next_fmt = changed_fmt(fmt)
    bcap.grant('change-component-type', ct).post({
      'abbr' : '*',
      'description' : '******',
      'format' : next_fmt,
      'deadline' : deadline + 1,
      'mandatory' : not mandatory,
      'gracehours' : grace_hours + 1,
      'sizelimit' : size_limit + 1
    })

    self.assertEqual(0, len(ComponentType.objects.filter(abbr=abbr,\
      description=description, fmt=fmt, deadline=deadline, mandatory=mandatory,\
      grace_hours=grace_hours, size_limit=size_limit,\
      conference=self.conference)))
    self.assertEqual(1, len(ComponentType.objects.filter(abbr='*',\
      description='******', fmt=next_fmt, deadline=(deadline + 1),\
      mandatory=(not mandatory), grace_hours=(grace_hours + 1),\
      size_limit=(size_limit + 1))))

  def test_change_user_email(self):
    user = User.objects.all()[0]
    old_email = user.email
    username = user.username
    full_name = user.full_name
    roles = user.roles.all()
    old_num = len(User.objects.filter(email=old_email))

    bcap.grant('change-user-email', user).post({'email' : 'x' + old_email})

    self.assertEqual(old_num - 1, len(User.objects.filter(email=old_email)))
    self.assertEqual(1, len(User.objects.filter(email='x' + old_email,\
      username=username, full_name=full_name, roles=roles,\
      conference=self.conference)))
    self.assertEqual(0, len(User.objects.filter(email=old_email,\
      username=username, full_name=full_name, roles=roles,\
      conference=self.conference)))

  def test_get_papers_of_dv(self):
    new_dv = DecisionValue(targetable=True, abbr='?',\
      description='Status Unknown', conference=self.conference)
    new_dv.save()

    grant_data = {'conference' : self.conference, 'decision_value' : new_dv}
    get_cap = bcap.grant('get-papers-of-dv', grant_data)

    response = get_cap.get()
    self.assertEqual(len(response), 0)

    paper = Paper.objects.filter(title=\
      'An interactive logical language for a balanced functional network')[0]
    paper.target = new_dv
    paper.save()

    response = get_cap.get()
    self.assertEqual(len(response), 1)
    self.assertEqual(paper.id, response[0])

    other_paper = Paper.objects.filter(title=\
      'An active digital work cluster related to an active real-time display')[0]
    other_paper.target = new_dv
    other_paper.save()

    response = get_cap.get()
    self.assertEqual(len(response), 2)
    self.assertTrue(other_paper.id in response)
    self.assertTrue(paper.id in response)
