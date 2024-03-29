from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
  (r'^belay-frame/$', 'pltbelay.views.belay_frame'),
  (r'^request_account/$', 'pltbelay.views.request_plt_account'),
  (r'^request_account_silent/$', 'pltbelay.views.request_plt_account_silent'),
  (r'^glogin/$', 'pltbelay.views.glogin'),
  (r'^glogin_landing/.*$', 'pltbelay.views.glogin_landing'),
  (r'^plt_login/$', 'pltbelay.views.plt_login'),
  (r'^check_uname/$', 'pltbelay.views.check_uname'),
  (r'^check_login/$', 'pltbelay.views.check_login'),
  (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'^common.js', 'lib.py.common_js.common_js_handler')
)
