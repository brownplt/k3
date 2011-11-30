from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    (r'^.*/home$', 'contwinue.views.index_handler'),
    (r'^.*/getBasic$', 'contwinue.views.get_basic'),
    (r'^generate/$', 'contwinue.generate.generate')
)
