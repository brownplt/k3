import os
import subprocess
import settings
import logging
from lib.py.common import logWith404
from django.http import HttpResponse

logger = logging.getLogger('default')

def get_filetype(ofname):
  return subprocess.Popen(['file', '-bi', ofname],stdout=subprocess.PIPE).communicate()[0][:-1]


def file_response(filename, response_name):
    full_path = os.path.join(settings.SAVEDFILES_DIR, filename)

    try:
      full_file = open(full_path, 'r')
      file_data = full_file.read()
    except Exception as e:
      return logWith404(logger,\
        'file_response: exception reading file: %s' % e,\
        level='error')

    if file_data[0:4] == '%PDF':
      mimetype = 'application/pdf'
    else:
      mimetype = 'application/octet-stream'

    response = HttpResponse(file_data, mimetype=mimetype)
#    response['Content-Disposition'] = 'attachment; filename=%s' % response_name
    return response
