from contwinue.models import *
from django.http import HttpResponse
from lib.py.generate_tools import rand_str, rand_email, rand_bool
import logging
import sha
import random

logger = logging.getLogger('default')

def generate(request):
  """
  Generates sample data.
  Creates an admin/reviewer user (username: admin, pw: admin) and several 
  writer users (writer/writer, writer2/writer2, ..., writer10/writer10)
  """
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

  extended_abstracts = ComponentType.objects.filter(abbr='C')
  if len(extended_abstracts) == 0:
    extended_abstract = ComponentType(abbr='C', description='Extended Abstract',
      fmt='Text', size_limit=1000, deadline=int(time.time())+1, mandatory=False,
      grace_hours=96, conference=c)
    extended_abstract.save()

  writer_users = User.objects.filter(roles=writer_role)
  if len(writer_users) != 10:
    writer_user = User(username='writer', full_name='Joe Writer',
      email='joe@writer.com', password_hash=sha.new('writer').hexdigest(),
      conference=c)
    # 2 saves because you can't add ManyToMany relationships until the instance
    # is saved
    writer_user.save()
    writer_user.roles.add(writer_role)
    writer_user.save()
    
    for n in range(2, 11):
      nstr = str(n)
      writer_user = User(username='writer%s' % nstr, 
        full_name='Joe Writer%s' % nstr, email='joe@writer%s.com' % nstr, 
        password_hash=sha.new('writer%s' % nstr).hexdigest(), conference=c)
      writer_user.save()
      writer_user.roles.add(writer_role)
      writer_user.save()

  all_uus = UnverifiedUser.objects.all()
  if len(all_uus) != 10:
    for _ in range(10):
      uu = UnverifiedUser(name=rand_str(10), email=rand_email(),
        roletext=rand_str(10), conference=c)
      uu.save()

  all_topics = Topic.objects.all()
  if len(all_topics) != 10:
    topics = ['Programming Languages', 'Distributed Systems', 'Web Security', 
      'Computer Vision', 'Machine Learning', 'Computational Biology', 
      'Artificial Intelligence', 'Cryptography', 'Algorithms', 'Nanocomputing']
    for n in range(10):
      t = Topic(name=topics[n], conference=c)
      t.save()

  all_papers = Paper.objects.all()
  if len(all_papers) != 10:
    titles = [
      'A synchronized real-time cache related to a virtual secure technology',
      'An interactive secure compiler related to a synchronized binary interface',
      'An active functional solution embedded in an integrated functional agent',
      'A virtual functional compiler related to a collaborative programmable database',
      'An active digital work cluster related to an active real-time display',
      'An interactive logical language for a balanced functional network',
      'An integrated multimedia preprocessor derived from a scalable object-oriented agent',
      'An optimized multimedia language derived from a high-level watermarking network',
      'A dynamic binary preprocessor derived from a parameterized functional technology',
    ]
    for n in range(10):
      if n == 0:
        username = 'writer'
      else:
        username = 'writer%s' % str(n+1)
      contacts = User.objects.filter(username=username)
      contact = contacts[0]
      target = DecisionValue.objects.all()[random.randint(0, 2)] 
      p = Paper(contact=contact, author=contact.full_name, target=target,
        other_cats=rand_bool(), pc_paper=rand_bool(), hidden=False,
        conference=c)
      p.save()
      for _ in range(3):
        t = Topic.objects.all()[random.randint(0, 9)]
        t.papers.add(p)
        t.save()

  return HttpResponse('OK')
