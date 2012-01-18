import json

import settings as settings

from django.core import mail

import belaylibs.dj_belay as bcap
from belaylibs.models import Grant

from contwinue.tests_common import Generator, make_author
from contwinue.models import *
from contwinue.submitter import *
import contwinue.email_strings as strings


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

    self.assertEqual(len(response['authors']), 0)

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

  def test_get_component_file(self):
    f = open('testdata/testpdf.pdf', 'r')

    pcomp = ComponentType.objects.filter(abbr='P')[0]

    filesDict = {
      'P': f
    }
    textDict = {    }

    handler = PaperUpdateComponentsHandler()
    response = handler.post_files(self.paper, textDict, filesDict)

    self.assertEqual(bcap.dataPostProcess(response.content), True)

    aftercomponent = get_one(Component.objects.filter(type=pcomp, paper=self.paper))

    get_component = bcap.grant('get-component-file', aftercomponent)

    response = get_component.get()

    f2 = open('testdata/testpdf.pdf', 'r')
    self.assertEqual(response.content, f2.read())
    self.assertEqual(response.__getitem__('Content-Disposition'), 'attachment; filename=testdata/testpdf.pdf')
    f2.close()


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

    self.assertEqual(response['name'], 'Shriram Krishnamurthi')
    self.assertEqual(response['email'], 'sk@cs.fake')
    self.assertTrue(isinstance(response['remove'], bcap.Capability))

    uu = get_one(UnverifiedUser.objects.filter(email='sk@cs.fake'))
    self.assertTrue(not (uu is None))
    self.assertEqual(uu.name, 'Shriram Krishnamurthi')

    self.assertTrue(uu in paper.unverified_authors.all())

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, ['sk@cs.fake'])
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

    self.assertEqual(response['name'], existing_user.full_name)
    self.assertEqual(response['email'], user_email)
    self.assertTrue(isinstance(response['remove'], bcap.Capability))
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
      roletext='writer'
    )
    uu.save()

    launch_new_cap = bcap.dbgrant('launch-new-paper', {
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
      roletext='writer',
      conference=self.conference
    )
    uu.save()

    users_before = User.objects.all()

    launch_new_cap = bcap.dbgrant('launch-new-paper', {
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
      roletext='writer'
    )
    uu.save()

    paper = Paper.newPaper(
      contact=self.writer,
      title=u'Potions and Stuff',
      conference=self.conference,
    )
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
      roletext='writer',
      conference=self.conference
    )
    uu.save()

    paper = Paper.newPaper(
      contact=self.writer,
      title=u'Multicore Polyjuice Potion',
      conference=self.conference,
    )
    paper.save()

    authors_before = list(paper.authors.all())
    
    launch_cap = bcap.dbgrant('launch-attach-to-paper', {
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

    paper = Paper.newPaper(
      contact=user,
      title=u'Defense Against the Dark Farts',
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

    paper = Paper.newPaper(
      contact=minerva,
      title=u'Transmuting Groundskeepers to Professors',
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


