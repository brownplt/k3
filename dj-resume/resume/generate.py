import resume.models as rmod
import random
from django.http import HttpResponse
from datetime import date

def generate(request):
  cs_objs = rmod.Department.objects.filter(shortname='cs')
  if len(cs_objs) == 0:
    cs = rmod.Department(name='Computer Science', shortname='cs', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
  else:
    cs = cs_objs[0]
  
  ct_objs = rmod.ComponentType.objects.filter(short='ta')
  if len(ct_objs) == 0:
    ct = rmod.ComponentType(type='contactlong', name='type a', short='ta', department=cs)
    ct.save()
  else:
    ct = ct_objs[0]

  auth_objs = rmod.AuthInfo.objects.filter(email='matt@matt.com')
  auth = auth_objs[0]

  pos_objs = rmod.ApplicantPosition.objects.filter(name='pos1')
  if len(pos_objs) == 0:
    pos = rmod.ApplicantPosition(department=cs, name='pos1', shortform='p1',\
      autoemail=False)
    pos.save()
  else:
    pos = pos_objs[0]

  a_objs = rmod.Applicant.objects.filter(auth=auth)
  if len(a_objs) == 0:
    a = rmod.Applicant(auth=auth, firstname='john', lastname='doe', country='usa',\
      department=cs, position=pos)
    a.save()
  else:
    a = a_objs[0]

  c_objs = rmod.Component.objects.filter(applicant=a)
  if len(c_objs) == 0:
    c = rmod.Component(applicant=a, type=ct, value='component 1', lastSubmitted=0,\
      department=cs)
    c.save()
  else:
    c = c_objs[0]

  reviewer_objs = rmod.Reviewer.objects.filter(auth=auth)
  if len(reviewer_objs) == 0:
    reviewer = rmod.Reviewer(auth=auth, department=cs)
    reviewer.save()
  else:
    reviewer = reviewer_objs[0]

  review_objs = rmod.Review.objects.filter(applicant=a)
  if len(review_objs) == 0:
    review = rmod.Review(applicant=a, reviewer=reviewer, advocate='advocate',\
      comments='this shit sucks', draft=False, department=cs)
    review.save()
  else:
    review = review_objs[0]

  return HttpResponse('OK')
