from contwinue.models import *
from django.http import HttpResponse
import logging
import sha

logger = logging.getLogger('default')

def generate(request):
  conferences = Conference.objects.all()
  if len(conferences) == 0:
    c = Conference.make_new('Sample Conference', 'SC', 'admin', 'admin',
      'Joe Admin', 'joe@fake.com', False)
  else:
    c = conferences[0]

  writer_roles = Role.objects.filter(name='writer')
  if len(writer_roles) == 0:
    writer_role = Role(name='writer', conference=c)
    writer_role.save()
  else:
    writer_role = writer_roles[0]

  writer_bios = ComponentType.objects.filter(abbr='B')
  if len(writer_bios) == 0:
    writer_bio = ComponentType(abbr='B', description='Writer Bio', fmt='Any',
      size_limit=20000, deadline=int(time.time())+(86400*15), mandatory=False,
      grace_hours=48, conference=c)
    writer_bio.save()

  fave_colors = ComponentType.objects.filter(abbr='C')
  if len(fave_colors) == 0:
    fave_color = ComponentType(abbr='C', description='Favourite colour',
      fmt='Text', size_limit=10, deadline=int(time.time())+1, mandatory=False,
      grace_hours=96, conference=c)
    fave_color.save()

  writer_users = User.objects.filter(roles=writer_role)
  if len(writer_users) == 0:
    writer_user = User(username='writer', full_name='Joe Writer',
      email='joe@writer.com', password_hash=sha.new('writer').hexdigest(),
      conference=c)
    # 2 saves because you can't add ManyToMany relationships until the instance
    # is saved
    writer_user.save()
    writer_user.roles.add(writer_role)
    writer_user.save()

  return HttpResponse('OK')
