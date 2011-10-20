from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  (r'^$', 'apply.views.index_handler'),
  (r'cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'applicant/', 'apply.views.applicant_handler'),
  (r'new-account/', 'apply.views.new_account_handler'),
  (r'admin/', 'apply.views.admin_handler'),
  (r'^common.js$', 'lib.py.common_js.common_js_handler')
)

