from django.conf.urls.defaults import *
from metrolix import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #################### Backend Reporting server #################
    (r'^server/start_session', "metrolix.server.views.start_session"),
    (r'^server/report_result', "metrolix.server.views.report_result"),

    #################### Frontend API #################
    (r'^json_api/metrics_list/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_list"),

    (r'^json_api/sessions_list/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_sessions_list"),
    (r'^json_api/session_results/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_session_results"),
    (r'^json_api/delete_session', "metrolix.server.views.json_delete_session"),

    (r'^json_api/set_project', "metrolix.server.views.json_set_project"),
    (r'^json_api/metrics_data/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_data"),
    (r'^json_api/delete_result', "metrolix.server.views.json_delete_result"),


    #################### Frontend pages #################
    (r'^dashboard/metric/(?P<project>[\.A-z0-9_-]+)/(?P<path>.*)$', "metrolix.server.views.metric_details"),
    (r'^dashboard/metric_details$', "metrolix.server.views.metric_details_raw"),

    (r'^dashboard/metrics_view$', "metrolix.server.views.metrics_view_noproject"),
    (r'^dashboard/metrics_view/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.metrics_view"),

    (r'^dashboard/sessions_view$', "metrolix.server.views.sessions_view_noproject"),
    (r'^dashboard/sessions_view/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.sessions_view"),


    # Catch-all
    (r'^dashboard', "metrolix.server.views.index"),

    # Common media
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {"document_root": settings.MEDIA_ROOT}),

    ################### Admininistration frontend ################
    (r'^admin/', include(admin.site.urls)),
)
