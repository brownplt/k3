from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
  (r'^get_station/$', 'pltbelay.views.get_station'),
  (r'^create_plt_account/$', 'pltbelay.views.create_plt_account'),
  (r'^glogin/$', 'pltbelay.views.glogin'),
  (r'^glogin_landing/$', 'pltbelay.views.glogin_landing'),
  (r'^plt_login/$', 'pltbelay.views.plt_login'),
  (r'^check_uname/$', 'pltbelay.views.check_uname'),
  (r'^check_login/$', 'pltbelay.views.check_login'),
  (r'^make-stash/$', 'pltbelay.views.make_stash'),
  (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'^common.js', 'lib.py.common_js.common_js_handler')
)
