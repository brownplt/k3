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

# SendEmailsHandler
# Sends multiple emails to multiple users, with a few options
#   sendReviews: If 'yes', sends reviews for the user's paper(s)
#   stage: If 'preview', doesn't send emails, but returns them in json

# granted: |conference:Conference|
# -> {
#      stage: 'preview' or any,
#      sendReviews: 'yes' or any,
#      subject: String,
#      body: String,
#      users: [userid] or userid
#    }
# <- [{
#      Subject: String,
#      To: UserJSON,
#      Body: String
#    }]
#  or
#    {sent: 'sent'}
class SendEmailsHandler(bcap.CapHandler):
  def post_arg_names(self):
    return ['stage', 'sendReviews', 'subject', 'body', 'users']
  def post(self, granted, args):
    act = granted.conference.admin_contact
    users = args['users']
    subject = args['subject']
    sendReviews = args['sendReviews']
    body = args['body']
    stage = args['stage']
    if not isinstance(users, list):
      users = [users]
    useremails = []
    for uid in users:
      user = User.get_by_id(uid)
      paperemails = []
      if user is None:
        continue
      revtxt = ""
      if sendReviews == 'yes':
        papers = user.papers.all()
        for paper in papers:
          revtxt = u"\n-------\n"
          i = 1
          revs = []
          for review in paper.review_set.all():
            thisrev = u'Review %d:\n\n' % i
            if(not review.submitted):
              thisrev += u'Unsubmitted.\n\n'
            else:
              for comp in review.reviewcomponent_set.all():
                if not comp.type.pc_only:
                  thisrev += comp.value+u'\n\n'
            revs.append(thisrev)
          revtxt += u''.join(revs) + u'======'
          paperemails.append({'Subject':subject, 'To':user.to_json(), 'Body':body+revtxt})
      if paperemails == []:
        useremails.append({'Subject':subject, 'To':user.to_json(), 'Body':body+revtxt})
      else:
        useremails += paperemails
    if stage=='preview':
      return bcap.bcapResponse(useremails)
    else:
      for email in useremails:
        # send mail
        return bcap.bcapResponse({'sent': 'sent'})
