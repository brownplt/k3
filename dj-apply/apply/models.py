import belaylibs.models as bcap
from django.db import models


# TODO(matt): if these *Image fields represent file paths or URLs, 
# can we instead have ImageFields to store them in the DB as binary
# blobs?
class Department(bcap.Grantable):
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

class ApplicantPosition(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
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
  name = models.TextField()
  shortform = models.TextField()
  department = models.ForeignKey(Department)

class ScoreValue(bcap.Grantable):
  category = models.ForeignKey(ScoreCategory)
  number = models.IntegerField()
  explanation = models.TextField()
  department = models.ForeignKey(Department)

class Reviewer(bcap.Grantable):
  auth = models.ForeignKey(AuthInfo)
  committee = models.BooleanField()
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
  value = models.ForeignKey(ScoreValue)
  review = models.ForeignKey(Review)
  department = models.ForeignKey(Department)

class Area(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
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
  email = models.TextField()
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
