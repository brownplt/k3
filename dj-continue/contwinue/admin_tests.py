import time, datetime, os

import json

from django.core import mail
from django.test import TestCase

import contwinue.generate as generate
from contwinue.views import *
from contwinue.submitter import *
from contwinue.models import *
from belaylibs.models import Grant
import contwinue.email_strings as strings

import belaylibs.dj_belay as bcap

from contwinue.tests_common import Generator, has_keys

# Note:  These tests rely on generate.py, which creates an initial department
# and fills it in with some data.

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

class TestSetRole(Generator):
  def test_add(self):
    sherlock_acct = Account(key=str(uuid.uuid4()))
    sherlock_acct.save()
    sherlock = User(
      full_name=u'Sherlock Holmes',
      email=u'sherlock@gb.gov',
      conference=self.conference,
      account=sherlock_acct
    )
    sherlock.save()
    user = sherlock
    self.assertEqual(len(user.roles.all()), 0)

    set_role = bcap.grant('set-role', user)
    set_role.post({
      'role': 'reviewer',
      'value': 'panda-(any-value)'
    })

    self.assertEqual(len(user.roles.all()), 1)
    rev_role = Role.get_by_conf_and_name(self.conference, 'reviewer')
    self.assertEqual(user.roles.all()[0], rev_role)

  def test_remove(self):
    watson_acct = Account(key=str(uuid.uuid4()))
    watson_acct.save()
    watson = User(
      full_name=u'Doctor Watson',
      email=u'watson@gb.gov',
      conference=self.conference,
      account=watson_acct
    )
    watson.save()
    watson.roles.add(Role.get_by_conf_and_name(self.conference, 'reviewer'))
    user = watson
    self.assertEqual(len(user.roles.all()), 1)

    set_role = bcap.grant('set-role', user)
    set_role.post({
      'role': 'reviewer',
      'value': 'off'
    })

    self.assertEqual(len(user.roles.all()), 0)

  def test_add_ridiculous(self):
    mori_acct = Account(key=str(uuid.uuid4()))
    mori_acct.save()
    mori = User(
      full_name=u'Moriarty',
      email=u'mori@gb.gov',
      conference=self.conference,
      account=mori_acct
    )
    mori.save()
    user = mori
    self.assertEqual(len(mori.roles.all()), 0)

    set_role = bcap.grant('set-role', user)
    set_role.post({
      'role': 'not-a-real-role',
      'value': 'on'
    })

    self.assertEqual(len(user.roles.all()), 0)
