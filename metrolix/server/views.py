import time, datetime
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render_to_response
from metrolix.server.models import Project,Session, Metric,Result
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
    metrics = Metric.objects.filter(path=data["path"])
    if len(metrics) == 0:
        metric = Metric(path=data["path"], project = session.project)
        metric.save()
    else:
        metric = metrics[0]

    result = Result(session=session, metric = metric, value = data["value"])
    result.save()
    return HttpResponse("OK")

####################################################################
# Frontend
####################################################################

def metric_details(request, project, path):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")
    try:
        metric_obj = Metric.objects.get(path=path, project=proj_obj)
    except:
        return HttpResponseNotFound("Metric not found")

    return render_to_response("metric_details.html",
            {"metric": metric_obj, "results" : metric_obj.result_set.all()})

    return HttpResponse("project=%s path=%s" % (project, path))

def metric_list(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    metrics = Metric.objects.filter(project=proj_obj)
    print "HAVE %i" % len(metrics)

    for metric in metrics:
        metric.nb_values = len(metric.result_set.all())
        metric.last_value = 0

    return render_to_response("metric_list.html",
                {"project": proj_obj, "metrics" : metrics})

def json_metrics_list(request, project):
    try:
        proj_obj = Project.objects.get(name=project)
    except:
        return HttpResponseNotFound("Project not found")

    try:
      data = request.GET#simplejson.loads(request.raw_post_data)
    except:
      return HttpResponseBadRequest("Could not deserialize JSON request")

    metrics = Metric.objects.filter(project=proj_obj)

    if data.has_key("path_filter"):
        metrics = metrics.filter(path__contains=data["path_filter"])

    ret = []
    for metric in metrics:
        ret.append({"path" : metric.path, "title": metric.title,
                    "nb_values" : len(metric.result_set.all())})
    return HttpResponse(simplejson.dumps(ret))

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

    results = Result.objects.filter(metric__path__in=data.getlist("path"))
    for result in results:
        if not sessions.has_key(result.session.token):
            sessions[result.session.token] = {"date" : time.mktime(result.session.date.timetuple()), "values":[]}
            for i in xrange(0,len(metrics)):
                 sessions[result.session.token]["values"].append("undefined")
        sessions[result.session.token]["values"][path_to_idx[result.metric.path]] = result.value

    ret["sessions"] = sessions.values()
    ret["sessions"] = sorted(ret["sessions"], key = lambda x : x["date"])
#   for metric in metrics:
#        out_vals = []
#        results = Result.objects.filter(metric=metric)
#        if data.has_key("architecture"):
#            results = results.filter(session__host__architecture=data["architecture"])
#        #if data.has_key("host_name"):
#        #    metrics = metrics.filter(session__host__name=data["host_name"])
#        for result in results:
#            out_vals.append({"value": result.value, "date": time.mktime(result.session.date.timetuple())})
#
#        ret.append({"metric": {"path": metric.path, "title": metric.title},
#                    "values": out_vals})

    return HttpResponse(simplejson.dumps(ret))
