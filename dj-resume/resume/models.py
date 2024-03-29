import belaylibs.models as bcap
from django.db import models
import logging
import time
from django.core.cache import cache

logger = logging.getLogger('default')

def convert_time(secs):
  return time.strftime("%A, %B %d, %I:%M %p %Z",time.localtime(secs))

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
      'uname' : '%s (%s)' % (r.auth.name, r.auth.email),\
      'role' : r.auth.role} for r in reviewers]
  def findApplicants(self, email):
    auths = self.my(AuthInfo).filter(email=email)
    apps = []
    for auth in auths:
      apps += self.my(Applicant).filter(auth=auth)
    return apps
  def findRefs(self, email):
    refs = self.my(Reference).filter(email=email)
    return [{'appname' : r.applicant.firstname + ' ' + r.applicant.lastname,
      'appemail' : r.applicant.auth.email,
      'reference' : r} for r in refs]
  def update_basic(self):
    cache.delete('basic_%s' % self.id)
  def getBasic(self):
    cached_json = cache.get('basic_%s' % self.id, 'no-basic')
    if cached_json != 'no-basic':
      return cached_json
    basicJson = {\
      'info' : self.to_json(),\
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
      'degrees' : [d.to_json() for d in self.my(Degree)],\
    }
    cache.set('basic_%s' % self.id, basicJson)
    return basicJson
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
  def contact_json(self):
    return {\
      'name' : self.name,\
      'shortname' : self.shortname,\
      'contactName' : self.contactName,\
      'contactEmail' : self.contactEmail,\
      'techEmail' : self.techEmail\
    }
  # TODO(matt): bad to look up things by ID, but again, the frontend is written
  # this way
  def get_by_id(self, cls, id):
    objs = cls.objects.filter(id=id)
    if len(objs) > 0:
      return objs[0]
    return None
  def get_area_by_id(self, aid):
    return self.get_by_id(Area, aid)
  def get_position_by_id(self, pid):
    return self.get_by_id(ApplicantPosition, pid)
  def all_score_values(self):
    return ScoreValue.objects.filter(department=self)
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
    ('head-reviewer', 'head-reviewer'),\
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
  def save(self):
    super(bcap.Grantable, self).save()
    self.department.update_basic()
  def to_json(self):
    return {\
      'id' : self.id,\
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
  def save(self):
    super(bcap.Grantable, self).save()
    cache.set('applicant_%s' % self.id, self.to_json())  
  def myReviews(self):
    return Review.objects.filter(applicant=self, draft=False)\
      .exclude(advocate='comment')
  def getAreas(self):
    areas = self.area_set.all()
    areas_json = []
    for area in areas:
      a_json = area.to_json()
      weight = AreaWeight.objects.filter(applicant=self, area=area)
      if len(weight) == 0: a_json['weight'] = 0
      else: a_json['weight'] = weight[0].number
      areas_json.append(a_json)
    return areas_json
  def getReviews(self):
    return [r.to_json() for r in self.myReviews()]
  def getComponentTypeById(self, id):
    return ComponentType.objects.filter(id=id, department=self.department)
  def getComments(self):
    reviews = self.myReviews()
    return [{'id' : r.reviewer.id, 'rname' : r.reviewer.auth.name} for r in reviews]
  def getWeb(self):
    components = Component.objects.filter(applicant=self).exclude(value='')
    components = filter(lambda c: c.type.type == 'contactweb', components)
    return [{'name' : c.type.short, 'value' : c.value} for c in components]
  def get_submitted_objects(self):
    components = Component.objects.filter(applicant=self).exclude(lastSubmitted=0)
    components = filter(lambda c: c.type.type == 'statement', components)
    return components
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
  def get_component_objects(self):
    return self.component_set.all()
  def getComponents(self):
    return [c.to_json() for c in self.component_set.all()]
  def getComponentByType(self, component_type):
    return Component.objects.filter(department=self.department, applicant=self,\
      type=component_type)
  def getReferences(self):
    return [r.to_json() for r in self.reference_set.all()]
  def getReferencesModel(self):
    return [r for r in self.reference_set.all()]
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
  def getHighlights(self):
    highlights = Highlight.objects.filter(applicant=self)
    return [{'highlighteeName' : h.highlightee.auth.name} for h in highlights]
  def getHiddenUNames(self):
    hiddens = Hidden.objects.filter(applicant=self)
    return [h.reviewer.auth.name for h in hiddens]
  def getPairsOfReviewer(self, reviewer):
    return self.apprevpair_set.filter(reviewer=reviewer)
  def remove_area(self, area):
    self.area_set.remove(area)
    for aw in AreaWeight.objects.filter(applicant=self, area=area):
      aw.delete()
    self.save()
  def update_area(self, area, weight):
    if not (area in self.area_set.all()):
      self.area_set.add(area)
    weights = AreaWeight.objects.filter(area=area, applicant=self)
    if len(weights) == 0:
      aweight = AreaWeight(
        area=area,
        number=int(weight),
        applicant=self
      )
      aweight.save()
    else:
      for aw in weights:
        aw.number = int(weight)
        aw.save()
    self.save()
  def remove_areas(self):
    for a in Area.objects.filter(department=self.department, applicants=self):
      a.applicants.remove(self)
      a.save()
  def hide_from(self, reviewer):
    hiddens = Hidden.objects.filter(applicant=self, reviewer=reviewer)
    if len(hiddens) == 0:
      h = Hidden(applicant=self, reviewer=reviewer, department=self.department)
      h.save()
  def unhide_from(self, reviewer):
    Hidden.objects.filter(applicant=self, reviewer=reviewer).delete()
  def is_hidden_from(self, reviewer):
    return len(Hidden.objects.filter(applicant=self, reviewer=reviewer)) > 0
  def getReady(self):
    readies = ReadyApplicant.objects.filter(applicant=self)
    if(len(readies) == 0): return False
    else: return readies[0].ready
  def setReady(self, readiness=False):
    readies = ReadyApplicant.objects.filter(applicant=self)
    if(len(readies) == 0):
      re = ReadyApplicant(applicant=self, ready=readiness)
      re.save()
    else:
      readies[0].ready = readiness
      readies[0].save()
  def get_submitted_refs(self):
    return Reference.objects.filter(applicant=self).exclude(submitted=0)
  def to_json(self):
    return {
      'id' : self.id,
      'gender' : self.gender,
      'ethname' : self.ethnicity,
      'rejected' : self.rejected,
      'ready' : self.getReady(),
      'rtime' : self.rtime,
      'firstname' : self.firstname,
      'lastname' : self.lastname,
      'country' : self.country,
      'name' : self.firstname + ' ' + self.lastname,
      'areas' : self.getAreas(),
      'reviews' : self.getReviews(),
      'comments' : self.getComments(),
      'web' : self.getWeb(),
      'email' : self.auth.email,
      'statements' : self.getStatements(),
      'test_scores' : self.getTestScores(),
      'institutions' : self.institutions(),
      'referrals' : self.referrals(),
      'refletters' : self.getRefletters(),
      'components' : self.getComponents(),
      'position' : self.position.to_json(),
      'references' : self.getReferences(),
      'highlights' : self.getHighlights(),
      'hiddenunames' : self.getHiddenUNames()
    }
  def cache_id(self): return 'applicant_%s' % self.id
  def cached_json(self):
    cached = cache.get(self.cache_id(), 'no-app')
    if cached != 'no-app': return cached
    json = self.to_json()
    cache.set(self.cache_id(), json)
    return json
     
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

class ReadyApplicant(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  applicant = models.ForeignKey(Applicant)
  ready = models.BooleanField(default=False)

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
    return {'id' : self.id, 'name' : self.name, 'shortform' : self.shortform, 'values' : values}
  name = models.CharField(max_length=100)
  shortform = models.TextField()
  department = models.ForeignKey(Department)

class ScoreValue(bcap.Grantable):
  def to_json(self):
    return {'id' : self.id, 'number' : self.number, 'explanation' : self.explanation}
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
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  reviewer = models.ForeignKey(Reviewer)
  applicant = models.ForeignKey(Applicant)
  department = models.ForeignKey(Department)

class Review(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  advocate_choices = [\
    ('advocate', 'advocate'),\
    ('detract', 'detract'),\
    ('none', 'none'),\
    ('comment', 'comment')\
  ]
  def to_json(self):
    score_vals = [s.value.id for s in Score.objects.filter(review=self)]
    return {\
      'id' : self.id,\
      'rname' : self.reviewer.auth.name,\
      'reviewerName' : self.reviewer.auth.name,\
      'ord' : self.ord,\
      'advocate' : self.advocate,\
      'comments' : self.comments,\
      'scoreValues' : score_vals,\
      'draft' : self.draft\
    }
  def destroy_scores(self):
    for s in Score.objects.filter(review=self):
      s.delete()
  def get_new_score(self, val_id):
    # TODO(matt): this is the wrong way to do it, but the frontend is written
    # to pass ScoreValue IDs back and forth
    values = ScoreValue.objects.filter(id=val_id)
    if len(values) != 1:
      return None
    return Score(value=values[0], review=self, department=self.department)
  def transfer_scores_from(self, other):
    for other_score in Score.objects.filter(review=other):
      s = Score(value=other_score.value, review=self, department=self.department)
      s.save()
  def get_scores(self):
    return Score.objects.filter(review=self)
  applicant = models.ForeignKey(Applicant)
  reviewer = models.ForeignKey(Reviewer)
  ord = models.IntegerField(default=0)
  # TODO(matt): using choices may only have an effect through the Django
  # admin interface, and not on the actual data model. needs more research.
  advocate = models.TextField(choices=advocate_choices, default='none')
  comments = models.TextField()
  draft = models.BooleanField()
  department = models.ForeignKey(Department)

class Score(bcap.Grantable):
  def save(self):
    self.review.applicant.save()
    super(bcap.Grantable, self).save()
  def to_json(self):
    return {'score' : 'dummy field'}
  value = models.ForeignKey(ScoreValue)
  review = models.ForeignKey(Review)
  department = models.ForeignKey(Department)

class Area(bcap.Grantable):
  class Meta:
    unique_together = (('department', 'name'))
  def to_json(self):
    return {'id' : self.id, 'name' : self.name, 'abbr' : self.abbr}
  name = models.CharField(max_length=100)
  abbr = models.TextField()
  department = models.ForeignKey(Department)
  applicants = models.ManyToManyField(Applicant)

class AreaWeight(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  class Meta:
    unique_together =(('applicant', 'area'))
  number = models.IntegerField(default=0)
  area = models.ForeignKey(Area)
  applicant = models.ForeignKey(Applicant)

class Highlight(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  applicant = models.ForeignKey(Applicant)
  highlightee = models.ForeignKey(Reviewer)
  department = models.ForeignKey(Department)

class UnverifiedUser(bcap.Grantable):
  def belay_account(self):
    belay_creates = UnverifiedBelayAccount.objects.filter(uu=self)
    if len(belay_creates) > 1:
      raise Exception('Ambiguous belay_account')
    elif len(belay_creates) == 0:
      return None
    return belay_creates[0].create

  roles = [\
    ('applicant', 'applicant'),\
    ('reviewer', 'reviewer'),\
    ('admin', 'admin')\
  ]
  email = models.EmailField()
  name = models.TextField()
  role = models.TextField(choices=roles)
  department = models.ForeignKey(Department)

class UnverifiedBelayAccount(bcap.Grantable):
  uu = models.ForeignKey(UnverifiedUser)
  create = models.TextField()

class UnverifiedApplicant(bcap.Grantable):
  email = models.EmailField()
  department = models.ForeignKey(Department)
  position = models.ForeignKey(ApplicantPosition)

class PendingHighlight(bcap.Grantable):
  applicant = models.ForeignKey(Applicant)
  highlightee = models.ForeignKey(UnverifiedUser)
  department = models.ForeignKey(Department)

class Reference(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
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
  email = models.EmailField(unique=True)
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
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
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

class AppRevPair(bcap.Grantable):
  def save(self):
    self.applicant.save()
    super(bcap.Grantable, self).save()
  def get_reviews(self, draft):
    return Review.objects.filter(applicant=self.applicant,\
      reviewer = self.reviewer, draft=draft)
  def get_highlights(self):
    return Highlight.objects.filter(applicant=self.applicant,\
      highlightee=self.reviewer, department=self.applicant.department)
  applicant = models.ForeignKey(Applicant)
  reviewer = models.ForeignKey(Reviewer)
