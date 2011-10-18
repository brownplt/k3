from django.http import HttpResponseNotFound
import logging

def logWith404(logger, msg, level='info'):
  if level == 'debug':
    logger.debug(msg)
  if level == 'info':
    logger.info(msg)
  elif level == 'warn':
    logger.warn(msg)
  elif level == 'error':
    logger.error(msg)
  elif level == 'critical':
    logger.critical(msg)
  else:
    logger.warn('logWith404: invalid log level %s' % level)
    logger.warn('message was: ' % msg)
  return HttpResponseNotFound()
