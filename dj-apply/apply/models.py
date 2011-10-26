import belaylibs.models as bcap
from django.db import models


class Department(bcap.Grantable):
  def my(self, cls):
    return cls.objects.filter(department=self)
  def getPending(self):
    return self.my(UnverifiedUser).exclude(role='applicant')
  def getReviewers(self):
    reviewers = self.my(Reviewer)
    return [{'email' : r.auth.email,\
      'uname' : r.auth.username,\
      'name' : r.auth.name,\
      'role' : r.auth.role,\
      'committee' : r.committee } for r in reviewers]
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
  username = models.TextField()
  password_hash = models.TextField()
  email = models.EmailField()
  name = models.TextField()
  role = models.TextField(choices=roles)
  verify = models.IntegerField(default=0)
  department = models.ForeignKey(Department)

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
  name = models.TextField()
  shortform = models.TextField()
  autoemail = models.BooleanField()

class Applicant(bcap.Grantable):
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
  accepted = models.BooleanField(default=True)
  rtime = models.IntegerField(default=0)
  firstname = models.TextField()
  lastname = models.TextField()
  country = models.TextField()
  department = models.ForeignKey(Department)
  # TODO(matt): does the department of the ApplicantPosition have to be the same
  # as the department of this Applicant?
  position = models.ForeignKey(ApplicantPosition)

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
  name = models.TextField()
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
  committee = models.BooleanField()
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
  name = models.TextField()
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

class PendingHighlight(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  highlightee = models.ForeignKey(UnverifiedUser)
  department = models.ForeignKey(Department)

class Reference(bcap.Grantable):
  code = models.IntegerField()
  applicant = models.ForeignKey(Applicant)
  submitted = models.IntegerField()
  filesize = models.IntegerField()
  name = models.TextField()
  email = models.EmailField()
  department = models.ForeignKey(Department)
  lastRequested = models.IntegerField()

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
      'type' : self.type,\
      'value' : self.value,\
      'lastSubmitted' : self.lastSubmitted,\
      'verified' : self.verified,\
      'date' : str(self.date)\
    }
  # TODO(matt): effect of choices on data model?
  type = models.TextField(choices=choices)
  value = models.TextField()
  lastSubmitted = models.IntegerField()
  department = models.ForeignKey(Department)
  verified = models.BooleanField(default=False)
  date = models.DateField()

class Component(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  type = models.ForeignKey(ComponentType)
  value = models.TextField()
  lastSubmitted = models.IntegerField()
  department = models.ForeignKey(Department)
  verified = models.BooleanField(default=False)
  date = models.DateField()

class AuthCookie(bcap.Grantable):
  value = models.TextField()
  ipaddr = models.IPAddressField()
  user = models.ForeignKey(AuthInfo)
  expires = models.IntegerField()
