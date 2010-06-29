from django.conf.urls.defaults import *
from metrolix import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^server/start_session', "metrolix.server.views.start_session"),
    (r'^server/report_result', "metrolix.server.views.report_result"),

    (r'^dashboard/metric/(?P<project>[\.A-z0-9_-]+)/(?P<path>.*)$', "metrolix.server.views.metric_details"),
    (r'^dashboard/metrics_view$', "metrolix.server.views.metrics_view_noproject"),
    (r'^dashboard/metrics_view/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.metrics_view"),

    (r'^dashboard', "metrolix.server.views.index"),

    (r'^json_api/metrics_list/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_list"),
    (r'^json_api/set_project', "metrolix.server.views.json_set_project"),
    (r'^json_api/metrics_data/(?P<project>[\.A-z0-9_-]+)$', "metrolix.server.views.json_metrics_data"),

    # Common media                                                                                     
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {"document_root": settings.MEDIA_ROOT}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
