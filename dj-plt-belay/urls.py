from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^get_station/$', 'pltbelay.views.get_station'),
    (r'^create_plt_account/$', 'pltbelay.views.create_plt_account'),
    (r'^glogin/$', 'pltbelay.views.glogin'),
    (r'^plt_login/$', 'pltbelay.views.plt_login'),
    (r'^check_uname/$', 'pltbelay.views.check_uname'),
    (r'^check_login/$', 'pltbelay.views.check_login'),
)
