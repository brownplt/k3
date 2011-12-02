from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
  (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),

  (r'^.*/home$', 'contwinue.views.index_handler'),
  (r'^.*/getBasic$', 'contwinue.views.get_basic'),

  (r'^.*/create_user$', 'contwinue.views.create_user'),
  (r'^.*/get_launch$', 'contwinue.views.get_launch'),

  (r'^paper$', 'contwinue.views.paper'),

  (r'^glogin$', 'contwinue.accounts.glogin'),
  (r'^glogin_landing/.*', 'contwinue.accounts.glogin_landing'),
  (r'^generate/$', 'contwinue.generate.generate'),
  (r'^common.js', 'lib.py.common_js.common_js_handler')
)
