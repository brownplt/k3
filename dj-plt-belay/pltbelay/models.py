import belaylibs.models as bcap

from django.db import models

class BelayAccount(bcap.Grantable):
  station_url = models.CharField(max_length=200)

class PendingLogin(bcap.Grantable):
  # Key is for this server to trust the openID provider's request
  key = models.CharField(max_length=36)
  # ClientKey is a secret provided by the client to trust that new
  # windows were served from this server
  clientkey = models.CharField(max_length=36)

class PltCredentials(bcap.Grantable):
  username = models.CharField(max_length=200)
  salt = models.CharField(max_length=200)
  hashed_password = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

class GoogleCredentials(bcap.Grantable):
  identity = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

class BelaySession(bcap.Grantable):
  session_id = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

class Stash(bcap.Grantable):
  stashed_content = models.TextField(max_length=1000)

class PendingAccount(bcap.Grantable):
  email = models.TextField(max_length=100)
