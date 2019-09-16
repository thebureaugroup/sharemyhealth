from django.http import JsonResponse, Http404
from collections import OrderedDict
import requests
import json
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views.decorators.http import require_GET
from oauth2_provider.decorators import protected_resource
from .models import Crosswalk
from .utils import fhir_secured_request, fhir_get_access_token_with_client_credentials
__author__ = "Alan Viars"


FHIR_RESOURCE_TO_ID_MAP = OrderedDict()
FHIR_RESOURCE_TO_ID_MAP['Patient'] = ""
FHIR_RESOURCE_TO_ID_MAP['Observation'] = "subject"
FHIR_RESOURCE_TO_ID_MAP['Condition'] = "subject"
FHIR_RESOURCE_TO_ID_MAP['AllergyIntolerance'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Medication'] = ""
FHIR_RESOURCE_TO_ID_MAP['MedicationStatement'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['MedicationOrder'] = ""
FHIR_RESOURCE_TO_ID_MAP['DiagnosticReport'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Procedure'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['CarePlan'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Immunization'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Device'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Goal'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['ExplanationOfBenefit'] = "patient"
FHIR_RESOURCE_TO_ID_MAP['Coverage'] = ""


@require_GET
def fhir_metadata_endpoint(request):
    fhir_endpoint = "%s%s" % (settings.DEFAULT_FHIR_SERVER, "metadata")
    # print(fhir_endpoint)
    r = requests.get(fhir_endpoint)
    t = r.text
    t = replace_fhir_refrences(t)
    d = json.loads(t, object_pairs_hook=OrderedDict)
    # print(d["resourceType"])
    return JsonResponse(d)


@require_GET
@protected_resource()
def fhir_endpoint_with_id(request, fhir_resource, id):

    if fhir_resource not in settings.FHIR_RESOURCES_SUPPORTED:
        raise Http404

    cw = get_crosswalk(request)

    if fhir_resource == 'Patient':

        if id != cw.fhir_patient_id:
            raise Http404
    fhir_endpoint = "%s%s/%s" % (cw.fhir_source, fhir_resource, id)

    # print(fhir_endpoint)
    if cw.use_client_credentials:
        r = fhir_secured_request(fhir_endpoint,
                                 fhir_get_access_token_with_client_credentials())
    else:
        # We assume the FHIR server is accessible via VPN or other secure
        # network channel.
        r = requests.get(fhir_endpoint)

    t = r.text
    t = replace_fhir_refrences(t, back=cw.fhir_source)
    d = json.loads(t, object_pairs_hook=OrderedDict)
    # print(d["resourceType"])
    if d["resourceType"] == "OperationalOutcome":
        return JsonResponse(d)

    if fhir_resource not in (
        'Patient',
        'Medication',
            'Coverage'):  # The subject reference should exist
        try:
            subject_reference = d['subject']['reference'].split('/')[-1]
            if subject_reference != cw.fhir_patient_id:
                raise Http404
        except KeyError:
            raise Http404

    return JsonResponse(d)


@require_GET
@protected_resource()
def fhir_endpoint_search(request, fhir_resource):
    # Without an ID this is a search operation and return a Bundle
    if fhir_resource not in settings.FHIR_RESOURCES_SUPPORTED:
        raise Http404

    # Disallow patient search
    if fhir_resource == "Patient":
        return JsonResponse(patient_search_not_allowed_response())

    cw = get_crosswalk(request)
    fhir_patient_id = cw.fhir_patient_id
    fhir_endpoint = "%s%s" % (cw.fhir_source, fhir_resource)
    clean_get_params = OrderedDict()
    for k, v in request.GET.items():
        if k not in ("patient", "subject"):
            clean_get_params[k] = v

    patient_id_name = FHIR_RESOURCE_TO_ID_MAP[fhir_resource]

    if patient_id_name:
        clean_get_params[patient_id_name] = fhir_patient_id

    if cw.use_client_credentials:
        r = fhir_secured_request(fhir_endpoint,
                                 access_token=fhir_get_access_token_with_client_credentials(),
                                 params=clean_get_params,)
    else:
        # We assume the FHIR server is accessible via VPN or other secure
        # network channel.
        r = requests.get(fhir_endpoint, params=clean_get_params)

    t = r.text
    t = replace_fhir_refrences(t, back=cw.fhir_source)
    d = json.loads(t, object_pairs_hook=OrderedDict)

    if d["resourceType"] == "OperationOutcome":
        return JsonResponse(d)
    # if d["resourceType"] =

    # Iterate the Bundle to double check this is only the resource owner's data.
    # for e in d['entry']:
    #
    #     try:
    #         subject_reference = e['resource']['subject']['reference'].split('/')[-1]
    #         if subject_reference != cw.fhir_patient_id:
    #             raise Http404
    #     except KeyError:
    #         raise Http404

    return JsonResponse(d)


def get_user(request):
    try:
        user = request.resource_owner
    except AttributeError:
        user = request.user
    return user


def get_crosswalk(request):
    user = get_user(request)
    cw = get_object_or_404(Crosswalk, user=user)
    return cw


def patient_search_not_allowed_response():
    oo_response = OrderedDict()
    oo_response["resourceType"] = "OperationOutcome"
    oo_response["text"] = OrderedDict((
        ('status', 'generated'),
        ('div', """<div xmlns=\"http://www.w3.org/1999/xhtml\"><h1>Operation Outcome</h1>
                                        <table border=\"0\"><tr><td style=\"font-weight: bold;\">ERROR</td><td>[]</td>
                                        <td><pre>Patient search is not allowed on this server.</pre></td>
                                        \n\t\t\t\t\t\n\t\t\t\t\n\t\t\t</tr>\n\t\t
                                        </table>\n\t</div>""")))

    oo_response["issue"] = OrderedDict((
        ('severity', 'error'),
        ('code', 'processing'),
        ('diagnostics', 'Patient search is not allowed on this server'),
    ))
    return oo_response


def replace_fhir_refrences(text, back=settings.DEFAULT_FHIR_SERVER, front=settings.DEFAULT_OUT_FHIR_SERVER):
    text = text.replace(back[:-1], front)
    return text
