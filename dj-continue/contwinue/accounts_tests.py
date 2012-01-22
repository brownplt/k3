from django.core import mail

from belaylibs.models import Grant
import belaylibs.dj_belay as bcap

import contwinue.accounts as accounts
import contwinue.email_strings as strings
from contwinue.tests_common import Generator
from contwinue.models import get_one, UnverifiedUser

import settings

class TestCreateReviewer(Generator):
  def test_create(self):
    uu = accounts.new_reviewer(self.conference, 'Billy', 'billy@fake.edu')
    self.assertEqual(uu.conference, self.conference)
    self.assertEqual(uu.full_name, 'Billy')
    self.assertEqual(uu.email, 'billy@fake.edu')

  def test_email(self):
    settings.NO_MAIL = False
    uu = accounts.new_reviewer(self.conference, 'Bobby', 'bobby@fake.edu')
    accounts.send_new_reviewer_email(uu)

    self.assertEqual(len(mail.outbox), 1)

    self.assertEqual(
      mail.outbox[0].subject,
      strings.new_reviewer_subject % {
        'confname': uu.conference.name
      }
    )

    granted = get_one(Grant.objects.filter(
      internal_path='launch-reviewer',
      db_data=bcap.dbPreProcess(uu)
    ))
    self.assertTrue(granted is not None)

    self.maxDiff = None
    granted_cap = bcap.Capability(bcap.cap_url(granted.cap_id))
    
    self.assertEqual(
      mail.outbox[0].body,
      strings.new_reviewer_body % {
        'confname': uu.conference.name,
        'name': uu.full_name,
        'key': bcap.cap_for_hash(granted_cap),
        'base': bcap.this_server_url_prefix()
      }
    )

    settings.NO_MAIL = True

  def test_email_nonrev(self):
    uu = UnverifiedUser(
      conference=self.conference,
      name='Not-a-rev',
      email='not-rev@fake.edu',
      roletext='writer'
    )
    uu.save()
    try:
      accounts.send_new_reviewer_email(uu)
    except Exception as e:
      self.assertEqual(str(e), 'Tried to send reviewer email to writer')

