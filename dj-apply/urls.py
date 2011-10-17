from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
  (r'cap/.*', 'belaylibs.dj_belay.proxyHandler'),
  (r'applicant/', 'apply.views.applicant_handler'),
  #(r'scorecategory/', 'apply.views.scorecategory_test')
)

