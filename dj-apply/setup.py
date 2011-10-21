import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ
import settings
import belaylibs.dj_belay as bcap
from apply.models import UnverifiedUser, Department
from apply.views import ApplyInit
import sys

def setup(adminName):
  cses = Department.objects.filter(shortname='cs')
  if len(cses) == 0:
    cs = Department(name='Computer Science', shortname='CS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
  else:
    cs = cses[0]

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

