from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^server/start_session', "metrolix.server.views.start_session"),
    (r'^server/report_result', "metrolix.server.views.report_result"),

    (r'^dashboard/metric/(?P<project>[\.A-z0-9_-]+)/(?P<path>.*)$', "metrolix.server.views.metric_details"),
    (r'^dashboard/metric_list/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.metric_list"),

    (r'^json_api/metrics_list/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_list"),
    (r'^json_api/metrics_data/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_data"),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
