import time, datetime
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render_to_response
from metrolix.server.models import Project,Session, Metric,Result, Host, Report, ReportType, ProjectVersion
from metrolix.reports.json_unit import JSONUnitReportHandler
from django.views.decorators.csrf import csrf_exempt
from django.middleware import csrf
from django.core import serializers
import simplejson, logging

####################################################################
# Server API
####################################################################

server_logger = logging.getLogger("server")

@csrf_exempt
def start_session(request):
  try:
    if request.method != "POST":
      server_logger.error("POST request required")
      return HttpResponseBadRequest("POST request required")

    try:
      session_data = request.raw_post_data#request.POST["data"]
      session_request = simplejson.loads(session_data)
    except Exception, e:
      server_logger.error("Failed to deserialize JSON: %s" % e)
      return HttpResponseBadRequest("Could not deserialize JSON request")

    if not session_request.has_key("project_name"):
      server_logger.error("Project name not specified")
      return HttpResponseBadRequest("Project name not specified")

    try:
      project = Project.objects.get(name=session_request["project_name"])
    except:
      server_logger.error("Could not find project %s" % session_request["project_name"])
      return HttpResponseNotFound("Could not find project %s" % session_request["project_name"])

    version = session_request.get("version", None)
    branch = session_request.has_key("branch") and session_request.get("branch") or "trunk"

    if version is None:
      version = time.time()

    server_logger.error("Looking up project version %s %s" % (version, branch))
    project_versions = ProjectVersion.objects.filter(version=version, branch=branch)
    if len(project_versions) == 0:
      server_logger.error("Creating new project version %s - %s" % (version, branch))
      project_version = ProjectVersion(version=version, branch=branch, project=project)
      project_version.save()
    else:
      server_logger.info("Using existing project version %s - %s" % (version, branch))
      project_version = project_versions[0]

    session = Session(project_version = project_version)
    session.token = csrf._get_new_csrf_key()

    if session_request.has_key("host_info"):
      hi = session_request["host_info"]
      if not hi.has_key("name"):
        server_logger.error("Host name required")
        return HttpResponseBadRequest("host name required")
      h = Host.objects.filter(name = hi["name"])
      if len(h) > 0:
        h = h[0]
      else:
        h = Host(name = hi["name"])
        h.cpus = int(hi.get("cpus", "1"))
        h.ram_mb = int(hi.get("ram_mb", "0"))
        h.architecture = hi.get("architecture", "unknown")
        h.os = hi.get("os", "unknown")
        h.description = hi.get("description", "")
        h.save()
      session.host = h

    session.testset = session_request.get("testset", "All")
    session.name = session_request.get("session_name", "N/A")
    session.save()
    return HttpResponse(session.token)

  except Exception, e:
    server_logger.error("add_session failed: %s" % e)
    raise e

@csrf_exempt
def add_report(request):
  try:
    if request.method != "POST":
      server_logger.error("POST request required")
      return HttpResponseBadRequest("POST request required")

    try:
      data = simplejson.loads(request.raw_post_data)
    except Exception, e:
      server_logger.error("Failed to deserialize JSON: %s" % e)
      return HttpResponseBadRequest("Could not deserialize request")

    if not data.has_key("session_token"):
      server_logger.error("Session token not specified")
      return HttpResponseBadRequest("Session token not specified")
    if not data.has_key("name") or not data.has_key("type"):
      server_logger.error("Report name or type not specified")
      return HttpResponseBadRequest("Report name or type not specified")

    # Find the session
    try:
      session = Session.objects.get(token=data["session_token"])
    except:
      server_logger.error("Session %s not found" % data["session_token"])
      return HttpResponseNotFound("Could not find session (bad token: %s)" % data["session_token"])

    # Find the report type
    try:
      type = ReportType.objects.get(name = data["type"])
    except Exception, e:
      server_logger.error("Report type %s not found : %s" % (data["type"], e))
      return HttpResponseNotFound("Could not find report type %s" % data["type"])

    report = Report(name=data["name"], session = session, type = type)

    if data.has_key("text"):
      server_logger.info("Adding report with %s chars of text" % len(data["text"]))
      report.text = data["text"]
    elif data.has_key("path"):
      server_logger.info("Adding report with file: %s" % data["path"])
      report.path = data["path"]
    elif data.has_key("url"):
      server_logger.info("Adding report with URL: %s" % data["url"])
      report.url = data["url"]
    report.save()
    return HttpResponse("OK")

  except Exception, e:
    server_logger.error("add_report failed: %s" % e)
    raise e

@csrf_exempt
def report_result(request):
  try:
    if request.method != "POST":
      server_logger.error("POST request required")
      return HttpResponseBadRequest("POST request required")

    try:
      data =simplejson.loads(request.raw_post_data)
    except Exception, e:
      server_logger.error("Failed to deserialize JSON: %s" % e)
      return HttpResponseBadRequest("Could not deserialize request")

    if not data.has_key("session_token"):
      server_logger.error("Session token not specified")
      return HttpResponseBadRequest("Session token not specified")
    if not data.has_key("path") or not data.has_key("value"):
      server_logger.error("Path or value not specified")
      return HttpResponseBadRequest("Path or value not specified")

    # Find the session
    try:
      session = Session.objects.get(token=data["session_token"])
    except:
      server_logger.error("Session %s not found" % data["session_token"])
      return HttpResponseNotFound("Could not find session (bad token: %s)" % data["session_token"])

    # Retrieve or create the path info object
    metrics = Metric.objects.filter(path=data["path"],project=session.project_version.project)
    if len(metrics) == 0:
        metric = Metric(path=data["path"], project = session.project_version.project)
        if data.has_key("title"):
            metric.title = data["title"]
        if data.has_key("type"):
            metric.type = data["type"]
        metric.save()
    else:
        metric = metrics[0]

    result = Result(session=session, metric = metric, value = data["value"])
    result.save()
    return HttpResponse("OK")

  except Exception, e:
    server_logger.error("report_result failed: %s" % e)
    raise e


####################################################################
# Frontend API
####################################################################

def json_metrics_list(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    metrics = Metric.objects.filter(project=proj_obj)
    if request.GET.has_key("path_filter"):
        metrics = metrics.filter(path__contains=request.GET["path_filter"])

    metrics = metrics.order_by("path")

    ret = []
    for metric in metrics:
        ret.append({"path" : metric.path, "title": metric.title,
                    "nb_values" : len(metric.result_set.all())})
    return HttpResponse(simplejson.dumps(ret))

def json_sessions_list(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    sessions = Session.objects.filter(project_version__project=proj_obj)

    if request.GET.has_key("host"):
        sessions = sessions.filter(host__name__contains=request.GET["host"])
    if request.GET.has_key("os"):
        sessions = sessions.filter(host__os__contains=request.GET["os"])
    if request.GET.has_key("architecture"):
        sessions = sessions.filter(host__architecture__contains=request.GET["architecture"])

    if request.GET.has_key("branch"):
        sessions = sessions.filter(project_version__branch=request.GET["branch"])
    if request.GET.has_key("version"):
        sessions = sessions.filter(project_version__version=request.GET["version"])

    sessions = sessions.order_by("-date")

    ret = []
    for session in sessions:
        rs = {"date" : time.mktime(session.date.timetuple())}
        rs["token"] = session.token
        rs["sessionid"] = session.id
        rs["version"] = session.project_version.version
        rs["branch"] = session.project_version.branch
        rs["name"] = session.name
        rs["testset"] = session.testset
        if session.host is not None:
            rs["os"] = session.host.os
            rs["architecture"] = session.host.architecture
            rs["hostname"] = session.host.name
            rs["hostid"] = session.host.id
        ret.append(rs)
    return HttpResponse(simplejson.dumps(ret))

def json_session_results(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    results = Result.objects.filter(session__token=request.REQUEST["token"])
    results.order_by("metric__path")
    ret = []
    for result in results:
        rs = { "path": result.metric.path, "title": result.metric.title,
              "type": result.metric.type, "value": result.value}
        ret.append(rs)
    return HttpResponse(simplejson.dumps(ret))

def json_session_reports(request):
    reports = Report.objects.filter(session__token=request.REQUEST["token"])
    ret = []
    for report in reports:
        rs = { "name": report.name, "type": report.type.name }
        ret.append(rs)
    return HttpResponse(simplejson.dumps(ret))

def json_set_project(request):
    request.session["project_name"] = request.REQUEST["project_name"]
    return HttpResponse("OK")


def json_metrics_data(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    try:
      data = request.REQUEST
    except:
      return HttpResponseBadRequest("Could not deserialize JSON request")

    ret = {}

    metrics = Metric.objects.filter(project=proj_obj, path__in=data.getlist("path"))
    path_to_idx = {}
    ret["metrics"] = []
    i = 0
    for metric in metrics:
        ret["metrics"].append({"path": metric.path, "title": metric.title})
        path_to_idx[metric.path] = i
        i=i+1

    sessions = {}

    results = Result.objects.filter(metric__path__in=data.getlist("path"),metric__project=proj_obj)
    for result in results:
        if not sessions.has_key(result.session.token):
            sessions[result.session.token] = {
              "date" : time.mktime(result.session.date.timetuple()),
              "name" : result.session.name,
              "testset" : result.session.testset,
              "version" : result.session.project_version.version,
              "branch" : result.session.project_version.branch,

            "values":[]}
            for i in xrange(0,len(metrics)):
                 sessions[result.session.token]["values"].append({"value":"undefined", "id": "undefined"})
        sessions[result.session.token]["values"][path_to_idx[result.metric.path]] = {
            "value" :result.value, "id" : result.id}

    ret["sessions"] = sessions.values()
    ret["sessions"] = sorted(ret["sessions"], key = lambda x : x["date"])
    return HttpResponse(simplejson.dumps(ret))

def json_comparable_results(request):
  data = request.raw_post_data#request.POST["data"]

  print data
  json = simplejson.loads(data)

  rows = []
  project = Project.objects.get(name=json["project"])

  if json.has_key("branch"):
    versions = ProjectVersion.objects.filter(project=project, branch=json["branch"])
  else:
    versions = ProjectVersion.objects.filter(project=project)

  columns = []
  for line in json["lines"]:
    columns.append("%s-%s" % (line["path"], line.get("session_name", "ALL")))

  # TODO Very slow
  for version in versions:
    row = ["%s-%s" % (version.version, version.branch)]
    print "Checking %s" % row[0]
    for line in json["lines"]:
      path = line["path"]
      session_name = line.get("session_name", None)
      if line.has_key("session_name"):
        results = Result.objects.filter(metric__path=path,session__project_version=version,
                                        session__name=line["session_name"])
      else:
        results = Result.objects.filter(metric__path=path, session__project_version=version)
      print "Results for %s / %s / %s: %i" % (row[0], path, session_name, len(results))
      if len(results) >= 1:
        row.append(results[0].value)
      else:
        row.append("NaN")
    rows.append(row)

  ret = { "rows" : rows, "columns" : columns }
  return HttpResponse(simplejson.dumps(ret), mimetype="application/json")

def json_delete_result(request):
    id = request.REQUEST["id"]
    Result.objects.get(pk=id).delete()
    return HttpResponse("ok")

def json_delete_session(request):
    token = request.POST["token"]
    Session.objects.get(token=token).delete()
    return HttpResponse("ok")

def json_html_report(request):
    session_token = request.POST["session_token"]
    report_name = request.POST["report_name"]
    try:
      report = Report.objects.get(session__token=session_token,name=report_name)
    except:
      server_logger.error("Report not found : session %s report %s" % (session_token, report_name))
      return HttpResponseNotFound("Report not found")

    # TODO Pluggable
    if report.type.name == "raw":
      return report.text
    elif report.type.name == "json_unit":
      h = JSONUnitReportHandler()
      return h.renderToText(report)

def json_html_compare_reports(request):
    session1_token = request.GET["session1_token"]
    session2_token = request.GET["session2_token"]
    report1_name = request.GET["report1_name"]
    report2_name = request.GET["report2_name"]

    try:
      report1 = Report.objects.get(session__token=session1_token,name=report1_name)
      report2 = Report.objects.get(session__token=session2_token,name=report2_name)
    except:
      return HttpResponseNotFound("Report not found")

    out =""
    if report1.type.name == "raw":
      return HttpResponseBadRequest("Cannot compare raw reports")
      out =  report.text
    elif report1.type.name == "json_unit":
      h = JSONUnitReportHandler()
      out = h.renderTextComparison(report1, report2)

    return HttpResponse(out, mimetype="text/plain")
####################################################################
# Frontend pages
####################################################################

def put_projects(request, template_dict):
  if not "project_name" in request.session:
      request.session["project_name"] = Project.objects.all()[0].name

  projects = Project.objects.all()
  template_dict["projects"] = []
  cur = None
  if "project_name" in request.session:
      cur = request.session["project_name"]
  for project in projects:
    if cur is not None and project.name == cur:
        old = template_dict["projects"]
        template_dict["projects"] = [project.name]
        template_dict["projects"].extend(old)
    else:
        template_dict["projects"].append(project.name)

def index(request):
    ret = {}
    put_projects(request, ret)
    return render_to_response("index.html", ret)

def metric_details_raw(request):
    return metric_details(request, request.session["project_name"], request.REQUEST["path"])

def metric_details(request, project, path):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")
    try:
        metric_obj = Metric.objects.get(path=path, project=proj_obj)
    except:
        return HttpResponseNotFound("Metric not found")

    ret =  {"metric": metric_obj, "results" : metric_obj.result_set.all().order_by("session__date")}
    put_projects(request, ret)
    return render_to_response("metric_details.html", ret)

def metrics_view_noproject(request):
    if not "project_name" in request.session:
        return HttpResponseNotFound("No project currently active")
    return metrics_view(request, request.session["project_name"])

def metrics_view(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    metrics = Metric.objects.filter(project=proj_obj)

    for metric in metrics:
        metric.nb_values = len(metric.result_set.all())
        metric.last_value = 0

    ret =  {"project": proj_obj, "metrics" : metrics}
    put_projects(request, ret)
    return render_to_response("metrics_view.html", ret)

def compare_metrics(request):
    if not "project_name" in request.session:
        return HttpResponseNotFound("No project currently active")
    project = request.session["project_name"]

    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    ret =  {"project": proj_obj}
    put_projects(request, ret)
    return render_to_response("compare_metrics.html", ret)

def sessions_view_noproject(request):
    if not "project_name" in request.session:
        return HttpResponseNotFound("No project currently active")
    return sessions_view(request, request.session["project_name"])

def sessions_view(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    ret =  {"project": proj_obj}
    put_projects(request, ret)
    return render_to_response("sessions_view.html", ret)
