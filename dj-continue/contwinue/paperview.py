
import contwinue.models as m
import belaylibs.dj_belay as bcap

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

