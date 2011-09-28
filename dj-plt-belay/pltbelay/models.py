import belaylibs.models as bcap

from django.db import models

class BelayAccount(bcap.Grantable):
  station_url = models.CharField(max_length=200)

class PltCredentials(bcap.Grantable):
  username = models.CharField(max_length=200)
  salt = models.CharField(max_length=200)
  hashed_password = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

# TODO: how to django google login?
"""
class GoogleCredentials(models.Model):
  user = db.UserProperty()
  account = db.ReferenceProperty(BelayAccount, required=True)
"""

class BelaySession(bcap.Grantable):
  session_id = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

