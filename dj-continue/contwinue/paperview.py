
import contwinue.models as m
import belaylibs.dj_belay as bcap
import time

class GetByRoleHandler(bcap.CapHandler):
  def post_arg_names(self): return ['role']
  def post(self, granted, args):
    role = m.Role.get_by_conf_and_name(granted.conference, args['role'])
    if role:
      return bcap.bcapResponse([u.to_json() for u in role.user_set.all()])
    else:
      return bcap.bcapResponse([])

class GetPaperHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(granted.paper.get_paper_with_decision())


# SaveReviewHandler
# Save a review (including rating, expertise, and text)
#
# granted: |review:Review|
# -> {
#  overallrating: Int,
#  expertiserating: Int,
#  subreviewer: Str,
#  comp-[0-9]*: maybe Str
# }
class SaveReviewHandler(bcap.CapHandler):
  def post(self, granted, args):
    prev = granted.review
    therev = prev.get_draft()
    if not therev:
      therev = prev.make_draft()
    therev.fill(**args)
    therev.save()

    if 'submit' in args and args['submit'] == 'yes':
      prev.submitted = True
      prev.fill(**args)
      conf.update_last_change(granted.review.paper)
      prev.save()

    return bcap.bcapResponse(therev.to_json())

class GetReviewHandler(bcap.CapHandler):
  def get(self, granted):
    user = granted['user'].user
    paper = granted['paper'].paper

    review = m.Review.get_published_by_user_and_paper(user, paper)
    if review:
      therev = review.get_draft()
      if not therev:
        therev = review.make_draft() 
      return bcap.bcapResponse({
        'hasPublished': review.submitted,
        'review': therev.to_json()
      })
    else:
      return bcap.bcapResponse(False)

class RevertReviewHandler(bcap.CapHandler):
  def post(self, granted, args):
    prev = granted.review
    therev = prev.get_draft()
    if therev:
      for c in therev.reviewcomponent_set.all():
        c.delete()
      therev.delete()
    therev = prev.make_draft()
    therev.last_saved = int(time.time())
    therev.save()
    return bcap.bcapResponse({
      'hasPublished': prev.submitted,
      'review': therev.to_json()
    })

class SetHiddenHandler(bcap.CapHandler):
  def post(self, granted, args):
    paper = granted.paper
    paper.hidden = args['hidden'] == 'yes'
    paper.conference.update_last_change(paper)
    paper.save()
    return bcap.bcapResponse(True)

class SetDeadlineHandler(bcap.CapHandler):
  def post(self, granted, args):
    paper = granted.paper
    tid = int(args['typeid'])
    thedl = m.get_one(paper.deadlineextension_set.filter(type__id=tid))
    if thedl:
      thedl.until = int(args['until'])
      thedl.save()
      return bcap.bcapResponse(thedl.to_json())
    else:
      thetype = m.ComponentType.get_by_id(int(args['typeid']))
      if thetype:
        de = m.DeadlineExtension(
          until=int(args['until']),
          conference=paper.conference,
          paper=paper,
          type=thetype
        )
        de.save()
        return bcap.bcapResponse(de.to_json())
    return bcap.bcapNullResponse()

class GetDeadlinesHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(
      [de.to_json() for de in granted.paper.deadlineextension_set.all()]
    )

class AssignReviewersHandler(bcap.CapHandler):
  def post(self, granted, args):
    paper = granted.paper
    conf = paper.conference
    assign = args['assign']
    if assign == '': assign = []
    if not isinstance(assign, list): assign = [assign]
    assign = [int(x) for x in assign]
    cur_reviews = m.Review.get_published_by_paper(paper)
    cur_reviewers = [r.reviewer for r in cur_reviews]
    cur_reviewer_ids = [r.id for r in cur_reviewers]

    for u in assign:
      if u not in cur_reviewer_ids:
        rev = m.Review(
          conference=conf,
          reviewer_id=u,
          paper=paper,
          overall=conf.default_overall,
          expertise=conf.default_expertise,
          published=True,
          last_saved=0
        )
        rev.save()
        draft = rev.get_draft()
        if draft is None: rev.make_draft()

    for u in cur_reviews:
      if u.reviewer.id not in assign:
        u.delete()

    conf.update_last_change(paper)
    return bcap.bcapResponse(True)

class LaunchPaperViewHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse({})

