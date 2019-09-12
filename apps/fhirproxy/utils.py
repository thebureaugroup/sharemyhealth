import requests
import urllib
from django.conf import settings


def fhir_get_access_token_with_client_credentials():
    data = urllib.parse.urlencode({"client_id": settings.BACKEND_FHIR_CLIENT_ID,
                                   "client_secret": settings.BACKEND_FHIR_CLIENT_SECRET,
                                   "resource": settings.BACKEND_FHIR_RESOURCE,
                                   "grant_type": "client_credentials"})
    response = requests.post(
        url=settings.BACKEND_FHIR_TOKEN_ENDPOINT, data=data)
    reply = response.json()
    # print(reply)
    return reply['access_token']


def fhir_secured_request(fhir_endpoint, access_token, params={}):
    # print("Secure:", fhir_endpoint, params)
    # accesstoken = FhirSecurity("https://nwt-staging.azurehealthcareapis.com")
    header = {"Authorization": "Bearer " + access_token}
    return requests.get(fhir_endpoint, headers=header, params=params)
