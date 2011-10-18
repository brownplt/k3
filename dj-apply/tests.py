import unittest
from apply.models import *
from apply.views import *

class UselessTest(unittest.TestCase):
  def setUp(self):
    pass

  def testUseless(self):
    self.assertEqual('true', 'true')
