import time, datetime
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render_to_response
from metrolix.server.models import Project,Session, Metric,Result, Host
from django.views.decorators.csrf import csrf_exempt
from django.middleware import csrf
from django.core import serializers
import simplejson

####################################################################
# Server API
####################################################################

@csrf_exempt
def start_session(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST request required")

    try:
      session_data = request.raw_post_data#request.POST["data"]
      session_request = simplejson.loads(session_data)
    except:
      return HttpResponseBadRequest("Could not deserialize request")

    if not session_request.has_key("project_name"):
      return HttpResponseBadRequest("Project name not specified")

    try:
      project = Project.objects.get(name=session_request["project_name"])
    except:
      return HttpResponseNotFound("Could not find project %s" % session_request["project_name"])

    session = Session(project = project)
    session.token = csrf._get_new_csrf_key()

    if session_request.has_key("host_info"):
        hi = session_request["host_info"]
        if not hi.has_key("name"):
            return HttpResponseBadRequest("host name required")
        h = Host.objects.filter(name = hi["name"])
        if len(h) > 0:
            h = h[0]
        else:
            h = Host(name = hi["name"])
            h.cpus = int(hi.get("cpus", "1"))
            h.ram_mb = int(hi.get("ram_mb", "0"))
            h.architecture = hi.get("architecture", None)
            h.os = hi.get("os", None)
            h.description = hi.get("description", None)
            h.save()
        session.host = h

    session.version = session_request.get("version")

    session.save()
    return HttpResponse(session.token)

@csrf_exempt
def report_result(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST request required")
    try:
      data =simplejson.loads(request.raw_post_data)
    except:
      return HttpResponseBadRequest("Could not deserialize request")

    if not data.has_key("session_token"):
      return HttpResponseBadRequest("Session token not specified")
    if not data.has_key("path") or not data.has_key("value"):
      return HttpResponseBadRequest("Path or value not specified")

    # Find the session
    try:
      session = Session.objects.get(token=data["session_token"])
    except:
      return HttpResponseNotFound("Could not find session (bad token: %s)" % data["session_token"])

    # Retrieve or create the path info object
    metrics = Metric.objects.filter(path=data["path"],project=session.project)
    if len(metrics) == 0:
        metric = Metric(path=data["path"], project = session.project)
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

    sessions = Session.objects.filter(project=proj_obj)

    if request.GET.has_key("host"):
        sessions = sessions.filter(host__name__contains=request.GET["host"])
    if request.GET.has_key("os"):
        sessions = sessions.filter(host__os__contains=request.GET["os"])
    if request.GET.has_key("architecture"):
        sessions = sessions.filter(host__architecture__contains=request.GET["architecture"])

    sessions = sessions.order_by("-date")

    ret = []
    for session in sessions:
        rs = {"date" : time.mktime(session.date.timetuple())}
        rs["token"] = session.token
        rs["sessionid"] = session.id
        rs["version"] = session.version
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
            sessions[result.session.token] = {"date" : time.mktime(result.session.date.timetuple()), "values":[]}
            for i in xrange(0,len(metrics)):
                 sessions[result.session.token]["values"].append("undefined")
        sessions[result.session.token]["values"][path_to_idx[result.metric.path]] = result.value

    ret["sessions"] = sessions.values()
    ret["sessions"] = sorted(ret["sessions"], key = lambda x : x["date"])
    return HttpResponse(simplejson.dumps(ret))

def json_delete_result(request):
    id = request.REQUEST["id"]
    Result.objects.get(pk=id).delete()
    return HttpResponse("ok")

def json_delete_session(request):
    token = request.POST["token"]
    Session.objects.get(token=token).delete()
    return HttpResponse("ok")

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
