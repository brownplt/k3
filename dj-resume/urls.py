from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  (r'^$', 'resume.views.index_handler'),
  (r'cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'applicant/', 'resume.views.applicant_handler'),
  (r'new-account/', 'resume.views.new_account_handler'),
  (r'admin/', 'resume.views.admin_handler'),
  (r'review/', 'resume.views.review_handler'),
  (r'appreview/', 'resume.view.appreview_handler'),
  (r'^common.js$', 'lib.py.common_js.common_js_handler')
)

