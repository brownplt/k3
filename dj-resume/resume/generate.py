import resume.models as rmod
import random
import logging
from django.http import HttpResponse
from datetime import date

logger = logging.getLogger('default')

def generate(request):
  cs_objs = rmod.Department.objects.filter(shortname='cs')
  if len(cs_objs) == 0:
    logger.info('created cs dept')
    cs = rmod.Department(name='Computer Science', shortname='cs', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
  else:
    logger.info('used pre-existing cs dept')
    cs = cs_objs[0]
  
  ct_objs = rmod.ComponentType.objects.filter(short='ta')
  if len(ct_objs) == 0:
    logger.info('created component type')
    ct = rmod.ComponentType(type='contactlong', name='type a', short='ta', department=cs)
    ct.save()
  else:
    logger.info('used existing component type')
    ct = ct_objs[0]

  ct_objs = rmod.ComponentType.objects.filter(short='stmt')
  if len(ct_objs) == 0:
    logger.info('created component type')
    ct = rmod.ComponentType(type='statement', name='Research Statement', short='stmt', department=cs)
    ct.save()
  else:
    logger.info('used existing component type')
    ct = ct_objs[0]

  auth_objs = rmod.AuthInfo.objects.all()
  if len(auth_objs) == 0:
    return HttpResponse("No auth_info objects to use")
  auth = auth_objs[0]

  pos_objs = rmod.ApplicantPosition.objects.filter(name='pos1')
  if len(pos_objs) == 0:
    logger.info('created app position')
    pos = rmod.ApplicantPosition(department=cs, name='pos1', shortform='p1',\
      autoemail=False)
    pos.save()
  else:
    logger.info('used existing app position')
    pos = pos_objs[0]

  a_objs = rmod.Applicant.objects.filter(auth=auth)
  if len(a_objs) == 0:
    logger.error('ERROR: created applicant')
    a = rmod.Applicant(auth=auth, firstname='john', lastname='doe', country='usa',\
      department=cs, position=pos)
    a.save()
  else:
    logger.info('used existing applicant')
    a = a_objs[0]

  c_objs = rmod.Component.objects.filter(applicant=a)
  if len(c_objs) == 0:
    logger.info('created component')
    c = rmod.Component(applicant=a, type=ct, value='component 1', lastSubmitted=0,\
      department=cs)
    c.save()
  else:
    logger.info('used existing component')
    c = c_objs[0]

  reviewer_objs = rmod.Reviewer.objects.filter(auth=auth)
  if len(reviewer_objs) == 0:
    logger.info('created reviewer')
    reviewer = rmod.Reviewer(auth=auth, department=cs)
    reviewer.save()
  else:
    logger.info('used existing reviewer')
    reviewer = reviewer_objs[0]

  review_objs = rmod.Review.objects.filter(applicant=a)
  if len(review_objs) == 0:
    logger.info('created review')
    review = rmod.Review(applicant=a, reviewer=reviewer, advocate='advocate',\
      comments='this shit sucks', draft=False, department=cs)
    review.save()
  else:
    logger.info('used existing review')
    review = review_objs[0]

  area_objs = rmod.Area.objects.filter(department=cs)
  if len(area_objs) < 2:
    a = rmod.Area(name='area two', abbr='a2', department=cs)
    a.save()
    a = rmod.Area(name='area one', abbr='a1', department=cs)
    a.save()

  score_cats = rmod.ScoreCategory.objects.filter(department=cs)
  if len(score_cats) == 0:
    sc = rmod.ScoreCategory(name='Awesomeness Level', shortform='AL', department=cs)
    sc.save()
  else:
    sc = score_cats[0]

  score_vals = rmod.ScoreValue.objects.filter(department=cs)
  if len(score_vals) == 0:
    for i in range(5):
      sv = rmod.ScoreValue(category=sc, number=i, explanation='%d level of awesome' % i,\
        department=cs)
      sv.save()

  return HttpResponse('OK')
