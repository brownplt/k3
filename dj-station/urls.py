from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    (r'^generate/$', 'station.views.generate'),
    (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),
    (r'^testpost/$', 'station.views.testpost'),
    (r'^jscaps/$', 'station.views.jscaps'),
)
