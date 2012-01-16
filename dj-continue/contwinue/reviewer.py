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
# -> { bid: Int, papers: [Int] }
# <- [bidJSON]
class UpdateBidsHandler(bcap.CapHandler):
  def post(self, granted, args):
    pass

