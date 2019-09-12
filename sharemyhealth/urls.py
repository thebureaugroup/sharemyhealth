"""smh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from apps.home.views import authenticated_home
from oauth2_provider import views
from apps.hie.decorators import check_ial_before_allowing_authorize
from django.views.generic import TemplateView
from . import signals  # noqa


__author__ = "Alan Viars"

admin.site.site_header = "OAuth2 and FHIR Server Admin"
admin.site.site_title = "OAuth2 and FHIR Server Admin Portal"
admin.site.index_title = "Share My Health: OAuth2 and FHIR Server Site Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    url('social-auth/', include('social_django.urls', namespace='social')),
    path('accounts/', include('apps.accounts.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^home/', include('apps.home.urls')),
    url(r"^o/authorize/$",
        check_ial_before_allowing_authorize(views.AuthorizationView.as_view()), name="authorize"),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^.well-known/', include('apps.wellknown.urls')),
    url(r'^api/', include('apps.api.urls')),
    url(r'^fhir/', include('apps.fhirproxy.urls')),
    url(r'^hie/', include('apps.hie.urls')),
    url(r'^rhio/', include('apps.hie.urls')),
    url(r'^hixny/', include('apps.hie.urls')),
    url(r'^testclient/', include('apps.testclient.urls')),
    path('data-source-agreement/', TemplateView.as_view(
        template_name='data-source-agreement.html'), name='data-source-agreement'),
    path('', authenticated_home, name='home'),

]
