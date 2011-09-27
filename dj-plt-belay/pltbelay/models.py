from django.db import models

class BelayAccount(models.Model):
  station_url = models.CharField(max_length=200)

class PltCredentials(models.Model):
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

class BelaySession(models.Model):
  session_id = models.CharField(max_length=200)
  account = models.ForeignKey(BelayAccount)

