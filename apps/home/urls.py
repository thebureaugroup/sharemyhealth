from django.conf.urls import url
from django.contrib import admin
from .views import authenticated_home, id_token_payload_json

admin.autodiscover()

urlpatterns = [
    url(r'id-token-payload', id_token_payload_json, name='id_token_payload_json'),
    url(r'', authenticated_home, name='home'),
]
