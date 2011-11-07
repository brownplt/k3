import belaylibs.models as bcap
from django.db import models
import logging
import time

logger = logging.getLogger('default')

def convert_time(secs):
  return time.strftime("%A, %B %d, %I:%M %p",time.localtime(secs))

class Department(bcap.Grantable):
  @classmethod
  def departmentByName(cls, name):
    depts = Department.objects.filter(shortname=name)
    if len(depts) == 0:
      raise Exception("No such department")
    elif len(depts) > 1:
      raise Exception("Shouldn't happen, more than one %s department" % name)
    else:
      return depts[0]
  def my(self, cls):
    return cls.objects.filter(department=self)
  def getPositions(self):
    return self.my(ApplicantPosition)
  def getPending(self):
    return self.my(UnverifiedUser).exclude(role='applicant')
  def getReviewers(self):
    reviewers = self.my(Reviewer)
    return [{'email' : r.auth.email,\
      'name' : r.auth.name,\
      'role' : r.auth.role} for r in reviewers]
  def findRefs(self, email):
    refs = self.my(Reference).filter(email=email)
    return [{'appname' : r.applicant.firstname + ' ' + r.applicant.lastname,
      'appemail' : r.applicant.auth.email} for r in refs]
  def getBasic(self):
    return {\
      'info' : self.to_json(),\
      'areas' : self.my(Area),\
      'positions' : [j.to_json() for j in self.my(ApplicantPosition)],\
      'components' : [c.to_json() for c in self.my(ComponentType)],\
      'genders' : ['Unknown', 'Male', 'Female'],\
      'ethnicities' : {\
        'am':'American Indian or Alaskan Native',\
        'as':'Asian or Pacific Islander',\
        'b':'Black, non-Hispanic',\
        'h':'Hispanic',\
        'w':'White, non-Hispanic',\
        'zo':'Other',\
        'zu':'Unknown'
      },\
      'countries' : list(set([a.country for a in self.my(Applicant)])),\
      'scores' : self.my(ScoreCategory),\
      'degrees' : [d.to_json() for d in self.my(Degree)],\
    }
  def to_json(self):
    return {\
      'name' : self.name,\
      'shortname' : self.shortname,\
      'lastChange' : self.lastChange,\
      'brandColor' : self.brandColor,\
      'contactName' : self.contactName,\
      'contactEmail' : self.contactEmail,\
      'techEmail' : self.techEmail\
    }
  name = models.TextField()
  shortname = models.TextField()
  lastChange = models.IntegerField()
  headerImage = models.FilePathField(blank=True)
  logoImage = models.FilePathField(blank=True)
  resumeImage = models.FilePathField(blank=True)
  headerBgImage = models.FilePathField(blank=True)
  brandColor = models.TextField()
  contactName = models.TextField()
  contactEmail = models.EmailField()
  techEmail = models.EmailField()

class AuthInfo(bcap.Grantable):
  roles = [\
    ('applicant', 'applicant'),\
    ('reviewer', 'reviewer'),\
    ('admin', 'admin')\
  ]
  email = models.EmailField()
  name = models.TextField()
  role = models.TextField(choices=roles)
  department = models.ForeignKey(Department)
  # NOTE(joe): These are REMOVED ON PURPOSE from the model, but kept for
  # documentary reasons during porting.  If you are inheriting this codebase
  # and confused sometime in 2014, you can safely delete these lines.
  # username = models.TextField()
  # password_hash = models.TextField()
  # verify = models.IntegerField(default=0)

class ApplicantPosition(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
  def to_json(self):
    return {\
      'name' : self.name,\
      'shortform' : self.shortform,\
      'autoemail' : self.autoemail
    }
  department = models.ForeignKey(Department)
  # Changing this because mysql complains about textfields' uniqueness
  name = models.CharField(max_length=100)
  shortform = models.TextField()
  autoemail = models.BooleanField()

class Applicant(bcap.Grantable):
  def myReviews(self):
    return Review.objects.filter(applicant=self, draft=False)\
      .exclude(advocate='comment')
  def getAreas(self):
    return [a.to_json() for a in self.department.my(Area)]
  def getReviews(self):
    reviews = self.myReviews()
    rtn = []
    for r in reviews:
      scores = Score.objects.filter(review=r) 
      rtn.append({\
        'id' : r.id,\
        'rname' : r.reviewer.auth.name,\
        'svals' : [s.value.id for s in scores]\
      })
    return rtn
  def getComponentTypeById(self, id):
    return ComponentType.objects.filter(id=id, department=self.department)
  def getComments(self):
    reviews = self.myReviews()
    return [{'id' : r.reviewer.id, 'rname' : r.reviewer.auth.name} for r in reviews]
  def getWeb(self):
    components = Component.objects.filter(applicant=self).exclude(value='')
    components = filter(lambda c: c.type.type == 'contactweb', components)
    return [{'name' : c.type.short, 'value' : c.value} for c in components]
  def getStatements(self):
    components = Component.objects.filter(applicant=self).exclude(lastSubmitted=0)
    components = filter(lambda c: c.type.type == 'statement', components)
    return [c.type.id for c in components]
  def getTestScores(self):
    return []
  def institutions(self):
    return []
  def referrals(self):
    return []
  def getRefletters(self):
    return []
  def getComponents(self):
    return [c.to_json() for c in Component.objects.filter(applicant=self)]
  def getComponentByType(self, component_type):
    return Component.objects.filter(department=self.department, applicant=self,\
      type=component_type)
  def getReferences(self):
    return [r.to_json() for r in Reference.objects.filter(applicant=self)]
  def getReferencesOfEmail(self, email):
    return [r.to_json() for r in Reference.objects.filter(applicant=self, email=email)]
  def componentUpdate(self, id, val):
    cts = ComponentType.objects.filter(department=self.department, id=int(id))
    if len(cts) > 0:
      ct = cts[0]
      oldcomps = Component.objects.filter(department=self.department,\
        applicant=self, type=ct)
      if len(oldcomps) > 0:
        oldcomp = oldcomps[0]
        oldcomp.value = val
        oldcomp.lastSubmitted = int(time.time())
      else:
        oldcomp = Component(applicant=self, type=ct, value=val,\
          lastSubmitted=int(time.time()), department=self.department)
      oldcomp.save()
  def to_json(self):
    return {
      'id' : self.id,
      'gender' : self.gender,
      'ethname' : self.ethnicity,
      'rejected' : self.rejected,
      'rtime' : self.rtime,
      'firstname' : self.firstname,
      'lastname' : self.lastname,
      'country' : self.country,
      'name' : self.firstname + ' ' + self.lastname,
      'areas' : self.getAreas(),
      'reviews' : self.getReviews(),
      'comments' : self.getComments(),
      'web' : self.getWeb(),
      'statements' : self.getStatements(),
      'test_scores' : self.getTestScores(),
      'institutions' : self.institutions(),
      'referrals' : self.referrals(),
      'refletters' : self.getRefletters(),
      'components' : self.getComponents(),
      'position' : self.position.to_json(),
      'references' : self.getReferences(),
    }
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
  json = models.TextField(default='')
  auth = models.ForeignKey(AuthInfo)
  gender = models.TextField(choices=genders, default='Unknown')
  ethnicity = models.TextField(choices=ethnicities, default='zu')
  rejected = models.BooleanField(default=False)
  rtime = models.IntegerField(default=0)
  firstname = models.TextField()
  lastname = models.TextField()
  country = models.TextField()
  department = models.ForeignKey(Department)
  # TODO(matt): does the department of the ApplicantPosition have to be the
  # same as the department of this Applicant?
  position = models.ForeignKey(ApplicantPosition)
  def fullname(self):
    return self.firstname + ' ' + self.lastname

class Degree(bcap.Grantable):
  def to_json(self):
    return {'name' : self.name, 'shortform' : self.shortform}
  name = models.TextField()
  shortform = models.TextField()
  department = models.ForeignKey(Department)

class ApplicantInstitution(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  name = models.TextField()
  degree = models.ForeignKey(Degree)
  start_date = models.DateField()
  end_date = models.DateField()
  major = models.TextField()
  gpa = models.FloatField()
  gpa_max = models.FloatField()
  department = models.ForeignKey(Department)
  lastSubmitted = models.IntegerField()
  transcript_file = models.TextField(blank=True)
  transcript_official = models.BooleanField(default=False)

class ScoreCategory(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
  def getValues(self):
    return ScoreValue.objects.filter(category=self)
  def to_json(self):
    values = [v.to_json() for v in self.getValues()]
    return {'name' : self.name, 'shortform' : self.shortform, 'values' : values}
  name = models.CharField(max_length=100)
  shortform = models.TextField()
  department = models.ForeignKey(Department)

class ScoreValue(bcap.Grantable):
  def to_json(self):
    return {'number' : self.number, 'explanation' : self.explanation}
  category = models.ForeignKey(ScoreCategory)
  number = models.IntegerField()
  explanation = models.TextField()
  department = models.ForeignKey(Department)

class Reviewer(bcap.Grantable):
  auth = models.ForeignKey(AuthInfo)
  department = models.ForeignKey(Department)

  def hiddenIds(self):
    hiddens = Hidden.objects.filter(reviewer=self)
    # TODO(joe): This is really stupid, but works.  Why can't I join from
    # a query set?
    return list(set([h.applicant.id for h in hiddens]))
  def highlightIds(self):
    highlights = Highlight.objects.filter(highlightee=self)
    return list(set([h.applicant.id for h in highlights]))
  def draftIds(self):
    reviews = Review.objects.filter(reviewer=self, draft=True)\
                .exclude(comments='')
    return list(set([r.applicant.id for r in reviews]))

  def getApplicants(self):
    # TODO(joe): This should be filtered by department, figure out filter
    applicants = Applicant.objects.all()
    return list(applicants)

  def getLastChange(self):
    return self.department.lastChange

class Hidden(bcap.Grantable):
  reviewer = models.ForeignKey(Reviewer)
  applicant = models.ForeignKey(Applicant)
  department = models.ForeignKey(Department)

class Review(bcap.Grantable):
  advocate_choices = [\
    ('advocate', 'advocate'),\
    ('detract', 'detract'),\
    ('none', 'none'),\
    ('comment', 'comment')\
  ]
  applicant = models.ForeignKey(Applicant)
  reviewer = models.ForeignKey(Reviewer)
  ord = models.IntegerField(default=0)
  # TODO(matt): using choices may only have an effect through the Djang
  # admin interface, and not on the actual data model. needs more research.
  advocate = models.TextField(choices=advocate_choices, default='none')
  comments = models.TextField()
  draft = models.BooleanField()
  department = models.ForeignKey(Department)

class Score(bcap.Grantable):
  def to_json(self):
    return {'score' : 'dummy field'}
  value = models.ForeignKey(ScoreValue)
  review = models.ForeignKey(Review)
  department = models.ForeignKey(Department)

class Area(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
  def to_json(self):
    return {'name' : self.name, 'abbr' : self.abbr}
  name = models.CharField(max_length=100)
  abbr = models.TextField()
  department = models.ForeignKey(Department)

class Highlight(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  highlightee = models.ForeignKey(Reviewer)
  department = models.ForeignKey(Department)

class UnverifiedUser(bcap.Grantable):
  roles = [\
    ('applicant', 'applicant'),\
    ('reviewer', 'reviewer'),\
    ('admin', 'admin')\
  ]
  email = models.EmailField()
  name = models.TextField()
  role = models.TextField(choices=roles)
  department = models.ForeignKey(Department)

class UnverifiedApplicant(bcap.Grantable):
  email = models.EmailField()
  department = models.ForeignKey(Department)
  position = models.ForeignKey(ApplicantPosition)

class PendingHighlight(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  highlightee = models.ForeignKey(UnverifiedUser)
  department = models.ForeignKey(Department)

class Reference(bcap.Grantable):
  def to_json(self):
    return {\
      'submitted' : self.submitted,\
      'submittedStr' : convert_time(self.submitted),\
      'filesize' : self.filesize,\
      'name' : self.name,\
      'institution' : self.institution,\
      'email' : self.email,\
      'lastRequested' : self.lastRequested,\
      'lastRequestedStr' : self.lastRequested
    }
  applicant = models.ForeignKey(Applicant)
  submitted = models.IntegerField(default=0)
  filesize = models.IntegerField()
  name = models.TextField()
  institution = models.TextField()
  email = models.EmailField()
  department = models.ForeignKey(Department)
  lastRequested = models.IntegerField(default=0)
  filename = models.TextField()

class ComponentType(bcap.Grantable):
  choices = [\
    ('contactlong', 'contactlong'),\
    ('contactshort', 'contactshort'),\
    ('contactweb', 'contactweb'),\
    ('statement', 'statement'),\
    ('test_score', 'test_score')\
  ]
  def to_json(self):
    return {\
      'id' : self.id,\
      'type' : self.type,\
      'name' : self.name,\
      'short' : self.short\
    }
  # TODO(matt): effect of choices on data model?
  type = models.TextField(choices=choices)
  name = models.TextField()
  short = models.TextField()
  department = models.ForeignKey(Department)

class Component(bcap.Grantable):
  def to_json(self):
    return {\
      'typeID' : self.type.id,\
      'value' : self.value,\
      'lastSubmitted' : self.lastSubmitted,\
      'lastSubmittedStr' : convert_time(self.lastSubmitted)\
    }
  applicant = models.ForeignKey(Applicant)
  type = models.ForeignKey(ComponentType)
  value = models.TextField()
  lastSubmitted = models.IntegerField()
  department = models.ForeignKey(Department)

class AuthCookie(bcap.Grantable):
  value = models.TextField()
  ipaddr = models.IPAddressField()
  user = models.ForeignKey(AuthInfo)
  expires = models.IntegerField()
