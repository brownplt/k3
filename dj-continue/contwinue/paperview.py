
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

