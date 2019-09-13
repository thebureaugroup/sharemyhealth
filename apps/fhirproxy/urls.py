from django.conf.urls import url
from django.contrib import admin
from .views import (fhir_endpoint_with_id, fhir_endpoint_search, fhir_metadata_endpoint)

admin.autodiscover()

urlpatterns = [
    url(r'R4/metadata/$', fhir_metadata_endpoint, name='fhir_metadata_uri'),
    url(r'R4/(?P<fhir_resource>[^/]+)/(?P<id>[^/]+)/$', fhir_endpoint_with_id, name='fhir_endpoint_with_id_oauth'),
    url(r'R4/(?P<fhir_resource>[^/]+)/$', fhir_endpoint_search, name='fhir_endpoint_search_oauth'),
]
