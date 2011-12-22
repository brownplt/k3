import logging

from lib.py.common import logWith404, make_get_handler

from contwinue.models import *
import belaylibs.dj_belay as bcap

logger = logging.getLogger('default')

#######################################
# Admin Handlers
#######################################

class GetAdminHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_admin())

class GetAllHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted.conference
    return bcap.bcapResponse(conference.get_all())

class AddTopicHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['name']

  def post(self, granted, args):
    conference = granted.conference
    name = args['name']

    if conference.has_topic_named(name):
      t = conference.get_topic_by_name(name)
    else:
      try:
        t = Topic(name=args['name'], conference=granted.conference)
        t.save()
      except Exception as e:
        return logWith404(logger, 'AddTopicHandler: %s' % e, level='error')

    return bcap.bcapResponse(t.to_json())

class DeleteTopicHandler(bcap.CapHandler):
  def delete(self, granted):
    topic = granted.topic
    try:
      topic.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteTopicHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddDecisionValueHandler(bcap.CapHandler):
  def post_arg_name(self):
    return ['abbr', 'description', 'targetable']

  def post(self, granted, args):
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']
    targetable = args['targetable']

    if conference.has_decision_value(targetable, abbr, description):
      ndv = conference.get_decision_value(targetable, abbr, description)
    else:
      try:
        ndv = DecisionValue(targetable=targetable, abbr=abbr, \
          description=description, conference=conference)
        ndv.save()
      except Exception as e:
        return logWith404(logger, 'AddDecisionValueHandler: %s' % e, level='error')

    return bcap.bcapResponse(ndv.to_json())

class DeleteDecisionValueHandler(bcap.CapHandler):
  def delete(self, granted):
    dv = granted.decisionvalue
    try:
      dv.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteDecisionHandler: %s' % e, level='error')
    return bcap.bcapNullResponse()

class AddReviewComponentTypeHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['description', 'pcOnly']

  def post(self, granted, args): 
    conference = granted.conference
    description = args['description']
    pc_only = args['pcOnly']

    if conference.has_rc_type(description, pc_only):
      rct = conference.get_rc_type(description, pc_only)
    else:
      try:
        rct = ReviewComponentType(description=description, pc_only=pc_only,\
          conference=conference)
        rct.save()
      except Exception as e:
        return logWith404(logger, 'AddReviewComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(rct.to_json())

class AddComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args): 
    conference = granted.conference
    abbr = args['abbr']
    description = args['description']

    if conference.has_component_type(abbr):
      ct = conference.component_type_by_abbr(abbr)
    else:
      try:
        ct = ComponentType(abbr=abbr, description=description,\
          fmt=args['format'], size_limit=args['sizelimit'],\
          deadline=args['deadline'], grace_hours=args['gracehours'],\
          mandatory=args['mandatory'], conference=conference)
        ct.save()
      except Exception as e:
        return logWith404(logger, 'AddComponentTypeHandler: %s' % e,\
          level='error')

    return bcap.bcapResponse(ct.to_json())

class DeleteComponentTypeHandler(bcap.CapHandler):
  def delete(self, granted):
    ct = granted.componenttype
    try:
      ct.delete()
    except Exception as e:
      return logWith404(logger, 'DeleteComponentType: %' % e,\
        level='error')
    return bcap.bcapNullResponse()

class ChangeComponentTypeHandler(bcap.CapHandler):
  # TODO(matt): if it turns out change args are always the same as create args,
  # put this on the model class in order to avoid repetition
  def post_arg_names(self):
    return ['format', 'abbr', 'description', 'sizelimit', 'deadline',\
      'gracehours', 'mandatory']

  def post(self, granted, args):
    ct = granted.componenttype
    ct.fmt = args['format']
    ct.abbr = args['abbr']
    ct.description = args['description']
    ct.size_limit = args['sizelimit']
    ct.deadline = args['deadline']
    ct.grace_hours = args['gracehours']
    ct.mandatory = args['mandatory']

    try:
      ct.save()
    except Exception as e:
      return logWith404(logger, 'ChangeComponentType: %' % e,\
        level='error')
    
    return bcap.bcapResponse(ct.to_json())

class ChangeUserEmailHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['email']

  def post(self, granted, args):
    user = granted.user
    try:
      user.email = args['email']
      user.save()
    except Exception as e:
      return logWith404(logger, 'ChangeUserEmailHandler: %s' % e,\
        level='error')

    return bcap.bcapResponse('true')

# In contwinue.py, this is handle_getIDsByDecision
# Here, instead of passing the decision value ID, the decision value is part
# of the grant
class GetPapersOfDVHandler(bcap.CapHandler):
  def get(self, granted):
    conference = granted['conference'].conference
    decision_value = granted['decision_value'].decisionvalue

    return bcap.bcapResponse(conference.papers_of_dv(decision_value))

# SetRoleHandler
# Turns a role for a given user on or off, depending on value
# granted: |user:User|
# -> {role: role-string, value: 'on' or any}
# <- True
class SetRoleHandler(bcap.CapHandler):
  def post_arg_names(self): return ['role', 'value']
  def post(self, granted, args):
    user = granted.user
    role = Role.get_by_conf_and_name(user.conference, args['role'])
    if role is not None:
      if args['value'] == 'off': user.roles.remove(role)
      else: user.roles.add(role)
    return bcap.bcapResponse(True)

# SetContactHandler
# Sets the conference's contact to a different user if that user is an
# administrator
# granted: |conference:Conference|
# -> {contactID: Number}
# <- True
class SetContactHandler(bcap.CapHandler):
  def post_arg_names(self): return ['contactID']
  def post(self, granted, args):
    conf = granted.conference
    cid = args['contactID']
    user = User.get_by_id(cid)
    if user is None:
      return bcap.bcapResponse({
        'error': True,
        'message': 'No user with id %s.' % cid
      })
    admin = Role.get_by_conf_and_name(conf, 'admin')
    if admin in user.roles.all():
      conf.admin_contact = user
      conf.save()
      return bcap.bcapResponse(True)
    else:
      return bcap.bcapResponse({
        'error': True,
        'message': 'User %s is not an admin' % cid
      })

