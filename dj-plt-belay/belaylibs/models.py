from django.db import models

class Grantable(models.Model):
  pass

class Grant(models.Model):
  cap_id = models.CharField(max_length=200)
  # internal URL passed to the cap handler
  internal_path = models.CharField(max_length=200)
  # reference to DB item passed to cap handler
  #db_entity = db.ReferenceProperty(required=True)
  db_entity = models.ForeignKey(Grantable, related_name="granted_entity")
