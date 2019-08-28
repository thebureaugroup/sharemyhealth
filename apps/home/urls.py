from django.conf.urls import url
from django.contrib import admin
from .views import authenticated_home, id_token_payload_json, fetch_cda

admin.autodiscover()

urlpatterns = [
    
    url(r'fecth-cda-from-hie', fetch_cda, name='fetch_cda'),
    url(r'', authenticated_home, name='home'),
    url(r'id-token-payload', id_token_payload_json, name='id_token_payload_json'),

    
    
    url(r'', authenticated_home, name='home'),
]
