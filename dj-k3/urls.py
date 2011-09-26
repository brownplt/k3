from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^get_station/$', 'pltbelay.views.get_station'),
    (r'^create_plt_account/$', 'pltbelay.views.create_plt_account'),
    (r'^glogin/$', 'pltbelay.views.glogin'),
    (r'^plt_login/$', 'pltbelay.views.plt_login'),
    # Examples:
    # url(r'^$', 'k3.views.home', name='home'),
    # url(r'^k3/', include('k3.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
