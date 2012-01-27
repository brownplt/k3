
import contwinue.models as m
import belaylibs.dj_belay as bcap
import time
import logging

logger = logging.getLogger('default')

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
    paper = granted['paper'].paper
    user = granted['user'].user
    response = paper.get_paper_with_decision(user)
    return bcap.bcapResponse(response)

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
      prev.save()

    prev.conference.update_last_change(prev.paper)

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
    if 'assign' in args:
      assign = args['assign']
    else:
      assign = []
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
          reviewer=m.get_one(m.User.objects.filter(id=u)),
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

def comments_response(paper):
  return bcap.bcapResponse(
    [c.to_json() for c in paper.comment_set.all()]
  )

class GetCommentsHandler(bcap.CapHandler):
  def get(self, granted):
    return comments_response(granted.paper)

class PostCommentHandler(bcap.CapHandler):
  def post(self, granted, args):
    p = granted['paper'].paper
    user = granted['user'].user
    c = m.Comment(
      commenter=user,
      paper=p,
      posted_at=int(time.time()),
      value=args['value']
    )
    c.save()
    return comments_response(p)

class LaunchPaperViewHandler(bcap.CapHandler):
  def get(self, granted):
    user = granted['user'].user
    conf = user.conference
    paper = granted['paper'].paper
    caps = {}
    if 'admin' in user.rolenames:
      caps['setDeadline'] = bcap.grant('set-deadline', paper)
      caps['getDeadlines'] = bcap.grant('get-deadlines', paper)
      caps['assignReviewers'] = bcap.grant('assign-reviewers', paper)
      caps['getByRole'] = bcap.grant('get-by-role', conf)
      caps['updateDecision'] = bcap.grant('update-decision', paper)
      caps['setHidden'] = bcap.grant('set-hidden', paper)

    caps['getPaper'] = bcap.grant('get-paper', {
      'paper': paper,
      'user': user
    })
    caps['updateBids'] = bcap.grant('update-bids', user)
    caps['postComment'] = bcap.grant('post-comment', {
      'user': user, 'paper': paper
    })
    caps['getComments'] = bcap.grant('get-comments', paper)

    component_caps = {}
    for c in paper.get_dcomps_safe(user):
      component_caps[c.id] = bcap.grant('get-component-file', c)
    caps['getComponents'] = component_caps

    request_caps = {}
    for c in paper.get_hidden_comps(user):
      request_caps[c.type_id] = bcap.grant('request-component-access', {
        'user': user,
        'component': c
      })
    caps['requestComponents'] = request_caps

    restpapers = m.Paper.objects.filter(id__gt=paper.id)

    if restpapers.count() > 0:
      #TODO(joe): abstract this pattern into a function
      caps['nextPaper'] = {
        'cap': bcap.cap_for_hash(
          bcap.grant('launch-paperview', {
            'user': user, 'paper': restpapers[0]
          })
        ),
        'id': restpapers[0].id
      }
    caps['backToList'] = "%s/review#%s" % (
      bcap.this_server_url_prefix(),
      bcap.cap_for_hash(bcap.grant('launch-reviewer', user))
    )

    rev = m.Review.get_published_by_user_and_paper(user, paper)
    if rev:
      caps['getReview'] = bcap.grant('get-review', {
        'user': user, 'paper': paper
      })
      caps['saveReview'] = bcap.grant('save-review', rev)
      caps['revertReview'] = bcap.grant('revert-review', rev)
    return bcap.bcapResponse({
      'basicInfo': conf.get_admin_basic(),
      'addPassword': bcap.regrant('add-password', user),
      'addGoogleAccount': bcap.regrant('add-google-account', user),
      'credentials': user.get_credentials(),
      'email': user.email,
      'currentUser': user.to_json(),

      'paperCaps': caps
    })
