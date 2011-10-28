import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ
import settings
import belaylibs.dj_belay as bcap
from apply.models import UnverifiedUser, Department, Applicant, ApplicantPosition, AuthInfo
from apply.views import ApplyInit
import sys


def make_some_applicants(cs):
  print("There are %s applicants." % len(Applicant.objects.all()))
  # skip this if students exist
  if len(Applicant.objects.all()) >= 2: return

  student = ApplicantPosition(name='Student', shortform='Student', autoemail=True, department=cs)
  student.save()

  a1auth = AuthInfo(email='bob@fake', name='Bob the Applicant', role='applicant', department=cs)
  a1auth.save()  

  a1 = Applicant(auth=a1auth, gender='Male', ethnicity='zo', firstname='Bob', lastname='Applicant', country='Namibia', department=cs, position=student)
  a1.save()

  a2auth = AuthInfo(email='henry@fake', name='Henry the Applicant', role='applicant', department=cs)
  a2auth.save()

  a1 = Applicant(auth=a2auth, gender='Male', ethnicity='w', firstname='Henry', lastname='Applicant', country='Zambia', department=cs, position=student)
  a1.save()

def setup(adminName):
  cses = Department.objects.filter(shortname='cs')
  if len(cses) == 0:
    cs = Department(name='Computer Science', shortname='cs', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
  else:
    cs = cses[0]

  make_some_applicants(cs)

  unverified_user = UnverifiedUser( \
    role='admin',
    name=adminName,
    email='default@fake',
    department=cs)
  unverified_user.save()

  ApplyInit().process_request(None)

  create_account = bcap.grant('add-admin', unverified_user)
  print("To get started, go here: %s/static/new_account.html#%s" % \
        (bcap.this_server_url_prefix(), create_account.serialize()))

if __name__ == '__main__':
  setup_environ(settings)
  setup(sys.argv[1])

