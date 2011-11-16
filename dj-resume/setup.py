import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ
import settings
import belaylibs.dj_belay as bcap
from resume.models import UnverifiedUser, Department, Applicant, ApplicantPosition, AuthInfo, ComponentType
from resume.views import ResumeInit
import sys


def startDeptDefault(adminName, adminEmail, techEmail, deptname, shortname):
  dept = Department(
    name=deptname,
    shortname=shortname,
    lastChange=0,
    headerImage='',
    logoImage='',
    resumeImage='',
    headerBgImage='',
    contactName=adminName,
    contactEmail=adminEmail,
    techEmail=techEmail)
  dept.save()

  unverified_user = UnverifiedUser( \
    role='admin',
    name=adminName,
    email=adminEmail,
    department=dept)
  unverified_user.save()

  ResumeInit().process_request(None)

  create_account = bcap.grant('get-admin-email-and-create', unverified_user)

  posn = ApplicantPosition(department=dept, name='Assistant Professor',
    shortform='AsstProf', autoemail=True)
  posn.save()

  c = ComponentType(department=dept,type='statement',name='Cover Letter',short='Cover')
  c.save()
  c = ComponentType(department=dept,type='statement',name='Curriculum Vitae',short='CV')
  c.save()
  c = ComponentType(department=dept,type='statement',name='Research Statement',short='Research')
  c.save()
  c = ComponentType(department=dept,type='statement',name='Teaching Statement',short='Teaching')
  c.save()
  c = ComponentType(department=dept,type='contactweb',name='Home Page',short='home')
  c.save()
  c = ComponentType(department=dept,type='contactweb',name='Application Web Page',short='app')
  c.save()
  c = ComponentType(department=dept,type='contactlong',name='Additional Information',short='addtl')
  c.save()

  return "To get started, go here: %s/new-account/#%s" % \
    (bcap.this_server_url_prefix(), create_account.serialize())

def newAdmin(deptshortname, adminName, adminEmail):
  depts = Department.objects.filter(shortname=deptshortname)
  if len(depts) == 1:
    dept = depts[0]
  else:
    raise Exception('Couldn\'t find department %s' % deptshortname)

  unverified_user = UnverifiedUser( 
    role='admin',
    name=adminName,
    email=adminEmail,
    department=dept)
  unverified_user.save()

  ResumeInit().process_request(None)

  create_account = bcap.grant('get-admin-email-and-create', unverified_user)

  return "To get started, go here: %s/new-account/#%s" % \
    (bcap.this_server_url_prefix(), create_account.serialize())
  

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
    email='%s@fake' % adminName,
    department=cs)
  unverified_user.save()

  ResumeInit().process_request(None)

  create_account = bcap.grant('get-admin-email-and-create', unverified_user)
  print("To get started, go here: %s/static/new_account.html#%s" % \
        (bcap.this_server_url_prefix(), create_account.serialize()))

if __name__ == '__main__':
  setup_environ(settings)
  setup(sys.argv[1])

