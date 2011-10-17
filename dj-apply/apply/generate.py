import apply.models as amod
from django.http import HttpResponse
from datetime import date

def generate(request):
  cs_objs = amod.Department.objects.filter(shortname='CS')
  if len(cs_objs) == 0:
    cs = amod.Department(name='Computer Science', shortname='CS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='blue', contactName='Donald Knuth', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    cs.save()
  else:
    cs = cs_objs[0]

  phil_objs = amod.Department.objects.filter(shortname='PHIL')
  if len(phil_objs) == 0:
    phil = amod.Department(name='Philosophy', shortname='PHIL', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Friedrich Nietzsche', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    phil.save()
  else:
    phil = phil_objs[0]

  math_objs = amod.Department.objects.filter(shortname='MATH')
  if len(math_objs) == 0:
    math = amod.Department(name='Mathematics', shortname='MATH', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Alonzo Church', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    math.save()
  else:
    math = math_objs[0]

  hist_objs = amod.Department.objects.filter(shortname='HIST')
  if len(hist_objs) == 0:
    history = amod.Department(name='History', shortname='HIST', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Abraham Lincoln', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    history.save()
  else:
    history = hist_objs[0]

  en_objs = amod.Department.objects.filter(shortname='ENGL')
  if len(en_objs) == 0:
    english = amod.Department(name='English', shortname='ENGL', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Ernest Hemingway', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    english.save()
  else:
    english = en_objs[0]

  bio_objs = amod.Department.objects.filter(shortname='BIO')
  if len(bio_objs) == 0:
    biology = amod.Department(name='Biology', shortname='BIO', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Bacteria Bro', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    biology.save()
  else:
    biology = bio_objs[0]

  phys_objs = amod.Department.objects.filter(shortname='PHYS')
  if len(phys_objs) == 0:
    physics = amod.Department(name='Physics', shortname='PHYS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='Albert Einstein', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    physics.save()
  else:
    physics = phys_objs[0]

  mus_objs = amod.Department.objects.filter(shortname='MUS')
  if len(mus_objs) == 0:
    music = amod.Department(name='Music', shortname='MUS', lastChange=0,\
      headerImage='', logoImage='', resumeImage='', headerBgImage='',\
      brandColor='black', contactName='J.S. Bach', contactEmail='test@example.com',\
      techEmail='tech@example.com')
    music.save()
  else:
    music = mus_objs[0]

  departments = [cs, phil, math, history, english, biology, physics, music]

  genders = [\
    ('Unknown', 'Unknown'),\
    ('Male', 'Male'),\
    ('Female', 'Female')\
  ]

  ethnicities = [
    ('am','American Indian or Alaskan Native'),\
    ('as','Asian or Pacific Islander'),\
    ('b','Black, non-Hispanic'),\
    ('h','Hispanic'),\
    ('w','White, non-Hispanic'),\
    ('zo','Other'),\
    ('zu','Unknown')\
  ]

  authinfo_roles = [\
    ('applicant', 'applicant'),\
    ('reviewer', 'reviewer'),\
    ('admin', 'admin')\
  ]

  reviewer_advocate_choices = [\
    ('advocate', 'advocate'),\
    ('detract', 'detract'),\
    ('none', 'none'),\
    ('comment', 'comment')\
  ]

  componenttype_choices = [\
    ('contactlong', 'contactlong'),\
    ('contactshort', 'contactshort'),\
    ('contactweb', 'contactweb'),\
    ('statement', 'statement'),\
    ('test_score', 'test_score')\
  ]

  def randComponentType():
    return componenttype_choices[random.randint(0, 4)]

  def randReviewerAdvocate():
    return reviewer_advocate_choices[random.randint(0, 3)]

  def randAuthInfoRole():
    return authinfo_roles[random.randint(0, 2)]

  def randDepartment():
    return departments[random.randint(0, 7)]

  def randGender():
    return genders[random.randint(0, 2)]

  def randEthnicity():
    return ethnicities[random.randint(0, 6)]

  def randBool():
    if random.random() > 0.5:
      return True
    return False

  def randStr(n):
    return ''.join([chr(random.randint(48, 90)) for x in range(n)])

  def randEmail():
    nm = ''.join([chr(random.randint(97, 122) for x in range(5))])
    dom = ''.join([chr(random.randint(97, 122) for x in range(5))])
    return nm + '@' + dom

  def randDate():
    return date.fromtimestamp(random.randint(0, 1318790434))

  def randAuthInfo():
    rtn = amod.AuthInfo(username=randStr(10), password_hash=randStr(15), email=randEmail(),\
      name=randStr(10), role=randAuthInfoRole(), department=randDepartment())
    rtn.save()
    return rtn

  def randDateAfter(start):
    sord = start.toordinal()
    return date.fromordinal(random.randint(sord, int(1.2 * sord)))

  def randApplicantPosition():
    rtn= amod.ApplicantPosition(department=randDepartment(), name=randStr(10),\
      shortform=randStr(5), autoemail=randEmail())
    rtn.save()
    return rtn

  def randApplicant():
    rtn = amod.Applicant(auth=randAuthInfo(), gender=randGender(),\
      ethnicity=randEthnicity(), firstname=randStr(10), lastname=randStr(10),\
      country=randstr(20), department=randDepartment(), position=randApplicantPosition())
    rtn.save()
    return rtn

  def randDegree():
    rtn = amod.Degree(name=randStr(10), shortform=randStr(5), department=randDepartment())
    rtn.save()
    return rtn

  def randApplicantInstitution():
    startdate = randDate()
    enddate = randDateAfter(startdate)
    rtn = amod.ApplicantInstitution(applicant=randApplicant(), name=randStr(10),\
      degree=randDegree(), start_date=startdate, end_date=enddate, major=randStr(10),\
      gpa=(random.random() * 4), gpa_max=4, department=randDepartment(),\
      lastSubmitted=0, transcript_file='')
    rtn.save()
    return rtn

  def randScoreCategory():
    rtn = amod.ScoreCategory(name=randStr(10), shortform=randStr(5),\
      department=randDepartment())
    rtn.save()
    return rtn

  def randScoreValue():
    cat = randScoreCategory()
    dept = randDepartment()
    vals = amod.ScoreValue.objects.filter(department=dept, category=cat)
    num = 1 + max([v.number for v in vals].push(0))
    rtn = amod.ScoreValue(category=cat, number=num, explanation=randStr(30), department=dept)
    rtn.save()
    return rtn

  def randReviewer():
    rtn = amod.Reviewer(auth=randAuthInfo(), committee=randBool(), \
      department=randDepartment())
    rtn.save()
    return rtn

  def randReview():
    rtn = amod.Review(applicant=randApplicant(), reviewer=randReviewer(),\
      advocate=randReviewerAdvocate(), comments=randStr(20), draft=randBool(),\
      department=randDepartment())
    rtn.save()
    return rtn

  def randScore():
    rtn = amod.Score(value=randScoreValue(), review=randReview(), \
      department=randDepartment())
    rtn.save()
    return rtn

  def randArea():
    rtn = amod.Area(name=randStr(10), abbr=randStr(5), department=randDepartment())
    rtn.save()
    return rtn

  def randHighlight():
    rtn = amod.Highlight(applicant=randApplicant(), highlightee=randReviewer(),\
      department=randDepartment())
    rtn.save()
    return rtn

  def randUnverifiedUser():
    rtn = amod.UnverifiedUser(email=randEmail(), name=randStr(10), role=randAuthInfoRole(),\
      verify=0, department=randDepartment())
    rtn.save()
    return rtn

  def randPendingHighlight():
    rtn = amod.PendingHighlight(applicant=randApplicant(), highlightee=randUnverifiedUser(),\
      department=randDepartment())
    rtn.save()
    return rtn

  def randReference():
    rtn = amod.Reference(code=random.randint(1, 100), applicant=randApplicant(),\
      submitted=random.randint(1, 100), filesize=random.randint(1, 100),\
      name=randStr(10), email=randEmail(), department=randDepartment(),\
      lastRequested=random.randint(1, 100))
    rtn.save()
    return rtn

  def randComponentType():
    rtn = amod.ComponentType(type=randComponentType(), value=randStr(10),\
      lastSubmitted=random.randint(1, 100), department=randDepartment(),\
      date=randDate())
    rtn.save()
    return rtn

  def randComponent():
    rtn = amod.Component(applicant=randApplicant(), type=randComponentType(),\
      value=randStr(10), lastSubmitted=random.randint(1, 100),\
      department=randDepartment(), date=randDate())
    rtn.save()
    return rtn

  def randAuthCookie():
    rtn = amod.AuthCookie(value=randStr(20), ipaddr=randIPAddr(), user=randAuthInfo(),\
      expires=random.randint(1, 100))
    rtn.save()
    return rtn

  return HttpResponse("OK")
