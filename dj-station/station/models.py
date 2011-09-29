import belaylibs.models as bcap

from django.db import models

class LaunchInfo(bcap.Grantable):
  url = models.CharField(max_length=200)
  # TODO: what is private_data?
  private_data = models.CharField(max_length=200)

class Relationship(bcap.Grantable):
  sid = models.CharField(max_length=200)


class RelationshipPair(bcap.Grantable):
  relationship = models.ForeignKey(Relationship)
  instance_id = models.CharField(max_length=200)
  launch_info = models.ForeignKey(LaunchInfo)
 

class StationData(bcap.Grantable):
  #key = models.BigIntegerField(primary_key=True)
  key = models.CharField(max_length=500, primary_key=True)

class InstanceData(bcap.Grantable):
  data = models.CharField(max_length=200)

class SectionData(bcap.Grantable):
  name = models.CharField(max_length=200)
  attributes = models.CharField(max_length=200)
