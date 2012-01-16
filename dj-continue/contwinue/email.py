import belaylibs.dj_belay as bcap
import settings
import smtplib

from django.core.validators import validate_email
from django.core.mail import send_mail

def notFoundResponse():
  message = 'We didn\'t recognize that email address.  Please check what you \
 entered and try again.'

  return bcap.bcapResponse({
    'emailError': True,
    'error': True,
    'message': message
  })

def emailErrorResponse():
  message = 'We had trouble sending your message.  If this problem \
persists, contact the system maintainer.'

  return bcap.bcapResponse({
    'emailError': True,
    'error': True,
    'message': message
  })

def send_and_log_email(subject, msg, address, fromaddr, logger):
  try:
    validate_email(address)
  except Exception as e:
    logger.error('Couldn\'t send email (bad address): %s' % e)
    return notFoundResponse()
  logger.info('Trying to send e-mail')
  if settings.NO_MAIL:
    logger.error('send log email:\n %s (From: %s) \n %s \n%s' % (subject, fromaddr, address, msg))
    return False
  try:
    send_mail(subject, msg, fromaddr, [address], fail_silently=False)
  except smtplib.SMTPRecipientsRefused as e:
    logger.error('Couldn\'t send email (refused): %s' % e)
    return notFoundResponse()
  except Exception as e:
    logger.error('Couldn\'t send email (unknown): %s' % e)
    return emailErrorResponse()
  logger.error('Sent real email:\n %s \n%s' % (address, msg))
  return False

