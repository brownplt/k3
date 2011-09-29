import belaylibs.models as bcap

from django.db import models

class LaunchInfo(bcap.Grantable):
  domain = models.CharField(max_length=200)
  url = models.CharField(max_length=200)
  private_data = models.TextField()

class Relationship(bcap.Grantable):
  sid = models.CharField(max_length=200)
  instance_id = models.CharField(max_length=200)
  launch_info = models.ForeignKey(LaunchInfo)

class StationData(bcap.Grantable):
  key = models.CharField(max_length=500, primary_key=True)

class SectionData(bcap.Grantable):
  name = models.CharField(max_length=200)
  attributes = models.CharField(max_length=200)
