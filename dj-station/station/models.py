import belaylibs.models as bcap

from django.db import models

class StationData(bcap.Grantable):
  sid = models.CharField(max_length=255, primary_key=True)

class LaunchInfo(bcap.Grantable):
  domain = models.CharField(max_length=200)
  url = models.CharField(max_length=200)
  private_data = models.TextField()
  public_data = models.TextField()

class Relationship(bcap.Grantable):
  station = models.ForeignKey(bcap.Grantable, related_name="station")
  instance_id = models.CharField(max_length=200)
  launch_info = models.ForeignKey(LaunchInfo)

class SectionData(bcap.Grantable):
  name = models.CharField(max_length=200)
  attributes = models.CharField(max_length=200)
