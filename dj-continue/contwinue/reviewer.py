import json
import belaylibs.dj_belay as bcap

import contwinue.models as m

from contwinue.submitter import make_user

from lib.py.common import toJSON

# GetPaperSummariesHandler
# Returns the summaries for papers, used in the filter list.
# Indicates conflicts and avoids showing inaccessible papers
#
# granted: |user:User|
# -> { lastChangeVal: Int }
# <- { changed: True, lastChangeVal: Int, summaries: [{
#   id: Int,
#   author: authorJSON,
#   title: String,
#   decision: decisionJSON,
#   target: targetJSON,
#   othercats: othercatJSON,
#   contactEmail: String,
#   topics: topicsJSON,
#   conflicts: conflictsJSON,
#   pcpaper: pcpaperJSON,
#   hidden: Boolean,
#   dcomps: dcompsJSON,
#   oscore: oscoreJSON
# }]
# U
# {changed: False}

class GetPaperSummariesHandler(bcap.CapHandler):
  def post(self, granted, args):
    user = granted.user
    conf = user.conference
    if conf.last_change == int(args['lastChangeVal']):
      return bcap.bcapResponse({'changed': False})

    if conf.summaries_json is not None and conf.summaries_json != '':
      return bcap.bcapStringResponse(conf.summaries_json)

    flds = ['id','author','title','decision','target','other_cats',\
            'contact_email','topics','conflicts','pc_paper','hidden',\
            'oscore']
    def getFlds(obj):
      r = {}
      memo = False
      if obj.can_see_reviews(user):
        if obj.json != '':
          return obj.json
        else:
          ourflds = flds + ['reviews_info']
          memo = True
      else:
        ourflds = flds
      if obj.has_conflict(user):
        r['hasconflict'] = True
      else:
        r['hasconflict'] = False

      for fld in ourflds:
        r[fld] = obj.__getattribute__(fld)
      r['dcomps'] = obj.get_dcomps_safe(user)
      ourjson = r
      if memo:
        obj.json = bcap.dataPreProcessV(ourjson)
        obj.save()
      return bcap.dataPreProcessV(ourjson)

    resp = '{"value":{"changed":true,"lastChange":%d,"summaries":[%s]}}' %\
        (conf.last_change, ','.join([getFlds(obj) for obj in conf.my(m.Paper)]))
    conf.summaries_json = resp
    conf.save()

    return bcap.bcapStringResponse(resp)


# GetAbstractsHandler
# Gets all the abstracts for a conference
#
# granted: |conference:Conference|
# <- [{ id: Int, value: String }]
class GetAbstractsHandler(bcap.CapHandler):
  def get(self, granted):
    conf = granted.conference
    return bcap.bcapResponse([{
        'id': p.id,
        'value': p.get_component(conf.display_component)['value']
      } for p in conf.my(m.Paper) \
    ])

# GetAbstractHandler
# Gets a particular abstract, by id
#
# granted: |conference:Conference|
# -> { id: Int }
# <- String U Null
class GetAbstractHandler(bcap.CapHandler):
  def post(self, granted, args):
    pass

# UpdateBidsHandler
# Updates the bids for a given user and paper set
#
# granted: |user:User|
# -> { bid: Int, papers: "" U Int U [Int] }
# <- [bidJSON]
class UpdateBidsHandler(bcap.CapHandler):
  def post_arg_names(self): return ['bid', 'papers']
  def post(self, granted, args):
    user = granted.user
    ret = []
    oldbid = -1
    papers = args['papers']
    bid = int(args['bid'])
    if papers == '': papers = []
    if not isinstance(papers, list): papers = [papers]
    for paper in papers:
      exbid = m.Bid.get_by_paper_and_bidder(paper, user)
      if exbid:
        oldbid = exbid.value_id
        exbid.value_id = bid
        exbid.save()
        ret.append(exbid)
      else:
        b = m.Bid(
          conference=user.conference,
          bidder=user,
          paper_id=paper,
          value_id=bid
        )
        b.save()
        ret.append(b)
    if bid == user.conference.conflict_bid_id or \
       oldbid == user.conference.conflict_bid_id:
      for paper in papers:
        user.conference.update_last_change(
          m.get_one(m.Paper.objects.filter(id=paper)))
    return bcap.bcapResponse([b.to_json() for b in ret])


# GetReviewPercentagesHandler
# Gets percentage complete for reviewers
#
# granted: |conference:Conference|
# <- [{id: Int, name: Str, percentage: Str}]
class GetReviewPercentagesHandler(bcap.CapHandler):
  def get(self, granted):
    rlist = m.Role.get_by_conf_and_name(granted.conference, 'reviewer').user_set.all()
    ret = []
    for user in rlist:
      allrevs = list(m.Review.get_published_by_reviewer(user))
      if len(allrevs) == 0:
        ret.append({'id':user.id,'name':user.full_name,'percentage':'N/A'})
      else:
        subrevs = [x for x in allrevs if x.submitted]
        ret.append({'id':user.id,'name':user.full_name,'percentage':str(int(float(len(subrevs))/float(len(allrevs))*100))+'%'})
    return bcap.bcapResponse(ret)

# GetAbstractHandler
# Gets the abstract for a single paper
#
# granted: |paper:Paper|
# <- Str U None
class GetAbstractHandler(bcap.CapHandler):
  def get(self, granted):
    paper = granted.paper
    return bcap.bcapResponse(
      paper.get_component(paper.conference.display_component)['value']
    )

# GetUserBidsHandler
# Gets all of a user's bids on non-hidden papers
#
# granted: |user:User|
# <- [ bidJSON ]
class GetUserBidsHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse([
      x.to_json() for x in granted.user.unhidden_bids()
    ])

# UpdateDecisionHandler
# Changes the decision on a paper based on id
#
# granted: |paper:Paper|
# -> {decision: Int}
# <- True
class UpdateDecisionHandler(bcap.CapHandler):
  def post(self, granted, args):
    d = m.DecisionValue.get_by_id(int(args['decision']))
    paper = granted.paper
    paper.decision = d
    paper.save()
    paper.conference.update_last_change(paper)
    return bcap.bcapResponse(True)

# UpdateDecisionByIdHandler
# Changes the decision on a paper based on id
#
# granted: |conference:Conference|
# -> {decision: Int, paper: Int}
# <- True
class UpdateDecisionByIdHandler(bcap.CapHandler):
  def post(self, granted, args):
    d = m.DecisionValue.get_by_id(int(args['decision']))
    paper = m.get_one(m.Paper.objects.filter(
      conference=granted.conference,
      id=int(args['paper'])
    ))
    paper.decision = d
    paper.save()
    paper.conference.update_last_change(paper)
    return bcap.bcapResponse(True)


def check_unverified(uu):
  maybe_real_user = uu.get_user()
  if maybe_real_user is not None:
    return maybe_real_user
  else:
    (account, maybe_real_user) = make_user(uu)
    launch = bcap.dbgrant('launch-reviewer', maybe_real_user)
    launchable = m.Launchable(
      account=account,
      launchbase='%s/reviewer' % bcap.this_server_url_prefix(),
      launchcap=bcap.cap_for_hash(launch),
      display=''
    )
    launchable.save()
    return maybe_real_user

# RequestComponentAccessHandler
# granted: {user: |user:User|, component: |component:Component|}

# -> {}
# <- Boolean
class RequestComponentAccessHandler(bcap.CapHandler):
  def post(self, granted, args):
    reviewer = granted['user'].user
    component = granted['component'].component

    grant = m.ComponentGrantRequest(
      reviewer=reviewer,
      component=component,
      conference=reviewer.conference,
      granted=False
    )
    grant.save()

    return bcap.bcapResponse(True)

class GetMeetingOrderHandler(bcap.CapHandler):
  def get(self, granted):
    return bcap.bcapResponse(
      m.MeetingOrder.get_order(granted.conference)
    )

class GetMeetingPaperHandler(bcap.CapHandler):
  def post(self, granted, args):
    return bcap.bcapResponse(
      m.MeetingOrder.get_paper(granted.conference, args['paper'])
    )

# LaunchReviewerHandler
# Gets info and caps for launching the reviewer page
class LaunchReviewerHandler(bcap.CapHandler):
  def get(self, granted):
    if hasattr(granted, 'unverifieduser'):
      reviewer = check_unverified(granted.unverifieduser)
    elif hasattr(granted, 'user'):
      reviewer = granted.user
    else:
      raise Exception('LaunchReviewer: granted is not (Unverified)User')
    conf = reviewer.conference
    papers = conf.my(m.Paper, True)
    papers_caps = {}
    for paper in papers:
      paper_caps = {}
      if not paper.has_conflict(reviewer):
        if 'admin' in reviewer.role_names():
          paper_caps['updateDecision'] = bcap.grant('update-decision', paper)
        paper_caps['getAbstract'] = bcap.grant('get-abstract', paper)
        paper_caps['launch'] = bcap.cap_for_hash(
          bcap.grant('launch-paperview', {'user': reviewer, 'paper': paper})
        )
        comps_caps = {}
        for component in paper.get_components_safe(reviewer):
          view_comp = bcap.dbgrant('get-component-file', component)
          comps_caps[component.type.id] = view_comp
        paper_caps['compsCaps'] = comps_caps
      papers_caps[paper.id] = paper_caps

    launchAdmin = "#"
    meeting_caps = {}
    launchMeeting = bcap.cap_for_hash(bcap.grant('launch-meeting', reviewer))
    meeting_caps['launchMeeting'] = launchMeeting
    meeting_caps['getPaper'] = bcap.grant('get-meeting-paper', conf)
    meeting_caps['getOrder'] = bcap.grant('get-meeting-order', conf)
    if 'admin' in reviewer.rolenames:
      launchAdmin = "%s/admin#%s" % (
        bcap.this_server_url_prefix(),
        bcap.cap_for_hash(bcap.grant('launch-admin', reviewer))
      )
      meeting_caps['setOrder'] = bcap.grant('set-meeting-order', conf)
      meeting_caps['jumpTo'] = bcap.grant('meeting-jump-to', conf)
      meeting_caps['endMeeting'] = bcap.grant('end-meeting', conf)

    users = conf.users_by_role_name('reviewer')
    users_caps = {}
    for user in users:
      user_caps = {
        'getUserBids': bcap.grant('get-user-bids', user)
      }
      users_caps[user.id] = user_caps


    return bcap.bcapResponse({
      'basicInfo': conf.get_admin_basic(),
      'addPassword': bcap.grant('add-password', reviewer),
      'addGoogleAccount': bcap.grant('add-google-account', reviewer),
      'credentials': reviewer.get_credentials(),
      'email': reviewer.email,
      'currentUser': reviewer.to_json(),
      'launchAdmin': launchAdmin,

      'meetingCaps' : meeting_caps,

      'paperCaps': papers_caps,
      'userCaps': users_caps,
      'getUserBids': bcap.grant('get-user-bids', reviewer),
      'getPaperSummaries':bcap.grant('get-paper-summaries',reviewer),
      'getPercentages': bcap.grant('get-review-percentages', conf),
      'getAbstracts': bcap.grant('get-abstracts', conf),
      'updateBids': bcap.grant('update-bids', reviewer),
    })

class LaunchMeetingHandler(bcap.CapHandler):
  def get(self, granted):
    reviewer = granted.user
    conf = reviewer.conference
    back_to_list = "%s/review#%s" % (
      bcap.this_server_url_prefix(),
      bcap.cap_for_hash(bcap.grant('launch-reviewer', reviewer))
    )
    meeting_caps = {}
    meeting_caps['backToList'] = back_to_list,
    meeting_caps['getPaper'] = bcap.grant('get-meeting-paper', conf)
    meeting_caps['getOrder'] = bcap.grant('get-meeting-order', conf)
    if 'admin' in reviewer.rolenames:
      meeting_caps['setOrder'] = bcap.grant('set-meeting-order', conf)
      meeting_caps['jumpTo'] = bcap.grant('meeting-jump-to', conf)
      meeting_caps['endMeeting'] = bcap.grant('end-meeting', conf)
      meeting_caps['updateDecision'] =\
        bcap.grant('update-decision-by-id', conf)

    return bcap.bcapResponse({
      'basicInfo': conf.get_admin_basic(),
      'meetingCaps': meeting_caps
    })
