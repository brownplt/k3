import belaylibs.dj_belay as bcap

import contwinue.models as m

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
    pass

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
        self.update_last_change(paper)
    return bcap.bcapResponse([b.to_json() for b in ret])

