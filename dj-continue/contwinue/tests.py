import time, datetime, os

from contwinue.views import *
from contwinue.models import *

import belaylibs.dj_belay as bcap

from contwinue.tests_common import Generator
from contwinue.admin_tests import TestAdminPage, TestSetRole, TestSetContact, \
    TestSendEmails, TestGetSubReviewers, TestAddPCs, TestConfigure
from contwinue.submitter_tests import TestAuthorLaunch, TestUpdateAuthorName, \
    TestRemoveAuthor
from contwinue.reviewer_tests import TestGetAbstracts, TestUpdateBids, \
    TestReviewPercentages, TestGetPaperSummaries, TestGetUserBids, \
    TestUpdateDecision
from contwinue.paperview_tests import TestGetByRole, TestGetPaper, \
    TestSaveReview, TestGetReview, TestRevertReview, TestSetHidden, \
    TestSetDeadline
from contwinue.accounts_tests import TestCreateReviewer
from contwinue.model_tests import TestPaperJsons, TestCJSONSpeed
from contwinue.crypt_tests import TestEnDecrypt

# Note:  These tests rely on generate.py, which creates an initial department
# and fills it in with some data.

class FakeHttp(object):
  def __init__(self, path, method):
    self.path_info = path
    self.method = method

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

