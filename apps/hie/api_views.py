import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict
from .models import HIEProfile
from ..accounts.models import UserProfile
from . import hixny_requests


@require_GET
@protected_resource()
def get_patient_fhir_content(request):
    user = request.resource_owner
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp, g_o_c = HIEProfile.objects.get_or_create(user=user)
    hie_data = hixny_requests.fetch_patient_data(user, hp, up)
    if not hie_data.get('error'):
        hp.__dict__.update(**hie_data)
        hp.save()
    if hp.fhir_content:
        return JsonResponse(json.loads(hp.fhir_content))
    else:
        return JsonResponse(hie_data)


@require_GET
@login_required
def get_patient_fhir_content_test(request):
    user = request.user
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = HIEProfile.objects.get(user=user)
    return JsonResponse(json.loads(hp.fhir_content))


@require_GET
@protected_resource()
def get_cda_in_json(request):
    user = request.resource_owner
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = HIEProfile.objects.get(user=user)
    data = OrderedDict()
    data['subject'] = up.subject
    data['patient'] = hp.mrn
    data['cda'] = hp.cda_content
    return JsonResponse(data)


@require_GET
@protected_resource()
def get_cda_raw(request):
    user = request.resource_owner
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = get_object_or_404(HIEProfile, user=user)
    return FileResponse(hp.cda_content, content_type='application/xml')


@require_GET
@login_required
def get_cda_in_json_test(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp = get_object_or_404(HIEProfile, user=request.user)
    data = OrderedDict()
    data['subject'] = up.subject
    data['patient'] = hp.mrn
    data['cda'] = hp.cda_content
    return JsonResponse(data)


@require_GET
@login_required
def get_cda_raw_test(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp = get_object_or_404(HIEProfile, user=request.user)
    return FileResponse(hp.cda_content, content_type='application/xml')
