import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ
import settings
import belaylibs.dj_belay as bcap
import contwinue.generate as g

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

def get_admin_launch(conf_shortname):
  ContinueInit().process_request(None)
  conf = models.Conference.objects.filter(shortname=conf_shortname)
  admin_role = models.Role.objects.filter(name='admin')[0]
  print('Admins: %s' % len(admin_role.user_set.all()))
  admin = admin_role.user_set.all()[0]
  print(admin.role_names())
  launch_admin = bcap.grant('launch-admin', admin)

  launch_url = '%s/admin#%s' % (
    bcap.this_server_url_prefix(),
    bcap.cap_for_hash(launch_admin)
  )

  print('You can launch the admin page at %s.' % (
    launch_url
  ))
  
if __name__ == '__main__':
  if sys.argv[1] == 'get_admin_launch':
    get_admin_launch(sys.argv[2])
  if sys.argv[1] == 'sample':
    g.generate()
  if sys.argv[1] == 'create':
    # Fill in creation options here for make_conference above
    pass
