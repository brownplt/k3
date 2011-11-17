from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  (r'^$', 'resume.views.index_handler'),
  (r'^cs/$', 'resume.views.cs_index_handler'),
  (r'^bhort/$', 'resume.views.bhort_index_handler'),
  (r'^contact/cs$', 'resume.views.cs_contact_handler'),
  (r'^contact/bhort$', 'resume.views.bhort_contact_handler'),
  (r'^cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'^applicant/$', 'resume.views.applicant_handler'),
  (r'^new-account/$', 'resume.views.new_account_handler'),
  (r'^new-applicant/$', 'resume.views.new_applicant_handler'),
  (r'^admin/$', 'resume.views.admin_handler'),
  (r'^review/$', 'resume.views.review_handler'),
  (r'^appreview/$', 'resume.views.appreview_handler'),
  (r'^submit-reference/$', 'resume.views.reference_handler'),
  (r'^common.js$', 'lib.py.common_js.common_js_handler'),
  (r'^generate/$', 'resume.generate.generate')
)
