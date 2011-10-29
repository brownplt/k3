import belaylibs.models as bcap

from django.db import models

class BelayAccount(bcap.Grantable):
  station_url = models.CharField(max_length=200)

class PendingLogin(bcap.Grantable):
  key = models.CharField(max_length=36)

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
  session = models.ForeignKey(BelaySession)
  stashed_content = models.CharField(max_length=200)
