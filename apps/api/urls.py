from django.conf.urls import include, url
from django.contrib import admin
from .views import CDAExample, logout_user


admin.autodiscover()

# Copyright Videntity Systems, Inc. 2019

v1 = [
     url(r'cda', CDAExample.as_view(), name='cda'),
     url('remote-logout', logout_user, name="remote_logout"),
]

urlpatterns = [
    url('v1/', include(v1)),
]
