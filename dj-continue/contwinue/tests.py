"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

import contwinue.generate as generate
from contwinue.models import *
from contwinue.views import get_basic

import belaylibs.dj_belay as bcap

class FakeHttp(object):
  def __init__(self, path, method):
    self.path_info = path
    self.method = method

class Generator(TestCase):
  def setUp(self):
    generate.generate(None)

class TestBasic(Generator):
  def test_basic(self):
    conf = Conference.get_by_shortname('SC')
    
    req = FakeHttp('/SC/getBasic', 'GET')
    response = bcap.dataPostProcess(get_basic(req).content)
    
    self.assertEqual(response['info']['name'], 'Sample Conference')
    self.assertEqual(response['info']['shortname'], 'SC')
    self.assertEqual(response['adminContact'], 'joe@fake.com')

