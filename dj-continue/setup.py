import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ
import settings
import belaylibs.dj_belay as bcap

import contwinue.models as models
from contwinue.views import ContinueInit
import sys

def start_conference(admin_name, admin_email, conf_name, shortname, use_ds):
  ContinueInit().process_request(None)
  conf = models.Conference.make_new(
    admin_name=admin_name,
    admin_email=admin_email,
    admin_user=admin_email,
    admin_password="",
    name=conf_name,
    shortname=shortname,
    use_ds=use_ds
  )

  admin = models.get_one(models.User.objects.filter(
    email=admin_email,
    conference=conf
  ))
  launch_admin = bcap.grant('launch-admin', admin)

  launch_url = '%s/admin#%s' % (
    bcap.this_server_url_prefix(),
    bcap.cap_for_hash(launch_admin)
  )

  print('%s has been created.  You can launch the admin page at %s.' % (
    conf.name,
    launch_url
  ))

