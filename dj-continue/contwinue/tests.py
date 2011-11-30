"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

import contwinue.generate as generate
from contwinue.models import *
from contwinue.views import *

import belaylibs.dj_belay as bcap

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
    cap = bcap.grant('get-writer-basic', conf)

    response = cap.get()

    self.assertEqual(response['info']['name'], 'Sample Conference')
    self.assertEqual(response['info']['shortname'], 'SC')

    self.assertEqual(len(response['topics']), 10)
    # Only 1 because we filter for targetables
    self.assertEqual(len(response['decisions']), 1)
    # make_new makes 2
    self.assertEqual(len(response['components']), 4)

class TestAuthorLaunch(Generator):
  def test_author_get(self):
    writer = User.objects.filter(username='writer')[0]
    paper = Paper.objects.filter(contact=writer)[0]

    cap = bcap.grant('get-writer-paper-info', {'writer': writer, 'paper': paper})

    response = cap.get()

    self.assertEqual(response['title'], 'A synchronized real-time cache related to a virtual secure technology')
    self.assertEqual(response['components'][0]['value'], 'This is actually pretty short')
    self.assertEqual(response['author'], 'Joe Writer')
    self.assertEqual(response['pcpaper'], False)
    self.assertEqual(response['othercats'], True)
    self.assertTrue(type(response['target']['id']), int)
    self.assertEqual(len(response['topics']), 3)


