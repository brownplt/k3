from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),
    (r'^belay/generate/', 'station.views.generate'),
    (r'^belay/launch/', 'station.views.launch'),
    (r'^instances/.*', 'station.views.instances')
    (r'^instance/.*', 'station.views.instance')
)
