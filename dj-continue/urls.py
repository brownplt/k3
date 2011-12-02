from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
  (r'^.*/home$', 'contwinue.views.index_handler'),
  (r'^.*/getBasic$', 'contwinue.views.get_basic'),
  (r'^glogin$', 'contwinue.accounts.glogin'),
  (r'^glogin_landing/.*', 'contwinue.accounts.glogin_landing'),
  (r'^generate/$', 'contwinue.generate.generate'),
  (r'^common.js', 'lib.py.common_js.common_js_handler')
)
