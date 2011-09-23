import hashlib
import logging
import os
import sys
import uuid

from google.appengine.api import users

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

def djangoSetup():
  # for some reason this doesn't 'stick'
  os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
djangoSetup()

from django.template.loader import render_to_string

class BelayAccount(db.Model):
  station_url = db.StringProperty()

class PltCredentials(db.Model):
  username = db.StringProperty(required=True)
  salt = db.StringProperty(required=True)
  hashed_password = db.StringProperty(required=True)
  account = db.ReferenceProperty(BelayAccount, required=True)

class GoogleCredentials(db.Model):
  user = db.UserProperty()
  account = db.ReferenceProperty(BelayAccount, required=True)

class BelaySession(db.Model):
  session_id = db.StringProperty()
  account = db.ReferenceProperty(BelayAccount, required=True)

class GetStationHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user is None:
      self.response.out.write("No station url, because no user")
    else:
      self.response.out.write("AppEngine thought there was a user")

class GoogleLoginHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    q = GoogleCredentials.all()
    q.filter("user =", user)
    results = q.fetch(2)

    if(len(results) > 1): raise Exception("FATAL: Multiple entries for GUser")

    if(len(results) == 0):
      account = BelayAccount(station_url="http://not-a-url")
      account.put()
      gc = GoogleCredentials(account=account, user=user)
      gc.put()
    else:
      gc = results[0]
      account = gc.account

    session_id = str(uuid.uuid4())
    session = BelaySession(account=account, session_id=session_id)
    session.put()

    self.response.headers.add_header('Set-Cookie', \
        'session=%s; expires=Sun,31-May-2040 23:59:59 GMT; path=/;' % \
        session_id)
    self.response.out.write("Success")


HASH_ITERATIONS = 20
def get_hashed(rawpassword, salt):
  salted = rawpassword + salt
  for i in range(HASH_ITERATIONS):
    m1 = hashlib.md5()
    m1.update(salted)
    salted = m1.hexdigest()

  logging.debug("Salted: %s" % salted)
  return salted

class CreatePltCredentials(webapp.RequestHandler):
  def post(self):
    username = self.request.get("username")
    rawpassword = self.request.get("password")
    salt = str(uuid.uuid4())

    hashed_password = get_hashed(rawpassword, salt)    

    account = BelayAccount(station_url="http://not-a-url")
    account.put()

    credentials = PltCredentials(username=username, \
      salt=salt, \
      hashed_password=hashed_password, \
      account=account)
    credentials.put()

    session_id = str(uuid.uuid4())
    logging.debug("Session id: %s" % session_id)
    session = BelaySession(session_id=session_id, account=account)
    session.put()

    self.response.headers.add_header('Set-Cookie', \
        'session=%s; expires=Sun,31-May-2040 23:59:59 GMT; path=/;' % \
        session_id)
    self.response.out.write("Success")

class UsernameHandler(webapp.RequestHandler):
  def post(self):
    username = self.request.get("username")
    q = PltCredentials.all()

    q.filter("username = ", username)
    results = q.fetch(1)

    if len(results) == 0:
      self.response.out.write('Available')
    else:
      self.response.out.write('Taken')

class CheckLoginHandler(webapp.RequestHandler):
  def get(self):
    session_id = self.request.cookies['session'] 
    q = BelaySession.all()
    q.filter("session_id = ", session_id)
    results = q.fetch(1)

    if len(results) == 0:
      self.response.out.write('false')
    else:
      self.response.out.write('true')

application = webapp.WSGIApplication(
  [('/get_station', GetStationHandler),
   ('/create_plt_account', CreatePltCredentials),
   ('/glogin', GoogleLoginHandler),
   ('/check_uname', UsernameHandler),
   ('/check_login', CheckLoginHandler)
  ],
  debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
    main()
