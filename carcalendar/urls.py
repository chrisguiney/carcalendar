from django.conf.urls import patterns, include, url

from django.contrib import admin

import carcal.urls


admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'', include(carcal.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
