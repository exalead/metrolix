from django.db import models

class Host(models.Model):
  name = models.CharField(max_length=200)
  cpus = models.IntegerField()
  ram_mb = models.IntegerField()
  architecture = models.CharField(max_length=30)
  os = models.CharField(max_length=100)
  description = models.CharField(max_length=200)

  def __unicode__(self):
     return self.name

class Project(models.Model):
  name = models.CharField(max_length=200)

  def __unicode__(self):
     return self.name

class Session(models.Model):
  project = models.ForeignKey(Project)
  date = models.DateTimeField(auto_now_add=True)
  token = models.CharField(max_length=36)
  host = models.ForeignKey(Host, null = True)

  testset  = models.CharField(max_length=200)
  version = models.CharField(max_length=200)

  def __unicode__(self):
     return "[SE:%s/%s/%s (%s - %s)]" % (self.project.name, self.testset, self.version, self.token, self.date)


class ReportType(models.Model):
  name = models.CharField(max_length=200)

  def __unicode__(self):
    return "[RT:%s]" % (self.name)

class Report(models.Model):
  session = models.ForeignKey(Session)
  name = models.CharField(max_length=200)

  # Inline reports
  text = models.TextField()
  # File-based reports
  path = models.CharField(max_length=200)

  type = models.ForeignKey(ReportType)

class Metric(models.Model):
  TYPES = (
    ("none", "None"),
    ("time_ms", "Time in MS"),
    ("time_s", "Time in S"),
    ("speed_KBPS", "Time in KBPS"),
    ("percent", "Percentage"),
  )
  project = models.ForeignKey(Project)
  path = models.CharField(max_length=200)
  type = models.CharField(max_length=200, choices = TYPES)
  title = models.CharField(max_length=210)

  def __unicode__(self):
     return "[METRIC:" +self.path +"]"

class Result(models.Model):
  session = models.ForeignKey(Session)
  metric = models.ForeignKey(Metric)
  value = models.FloatField()

  def __unicode__(self):
     return "[%s=%s]" % (self.metric.path, self.value)



class MultiSession(models.Model):
  """
  A multi-session is created manually. It waits for several reports
  from several sessions for a maximum amount of time before performing its
  alerting work
  """

  def __unicode__(self):
    return "?"
