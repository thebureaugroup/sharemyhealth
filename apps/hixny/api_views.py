from django.http import JsonResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict
from .models import HIXNYProfile
from ..accounts.models import UserProfile
from django.contrib.auth.decorators import login_required
import json


@require_GET
@protected_resource()
def get_patient_fhir_content(request):
    user = request.resource_owner
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = HIXNYProfile.objects.get(user=user)
    return JsonResponse(json.loads(hp.fhir_content))

@require_GET
@login_required
def get_patient_fhir_content_test(request):
    user = request.user
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = HIXNYProfile.objects.get(user=user)
    return JsonResponse(json.loads(hp.fhir_content))


@require_GET
@protected_resource()
def get_cda_in_json(request):
    user = request.resource_owner
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    hp = HIXNYProfile.objects.get(user=user)
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
    hp = get_object_or_404(HIXNYProfile, user=user)
    return FileResponse(hp.cda_content, content_type='application/xml')


@require_GET
@login_required
def get_cda_in_json_test(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp = get_object_or_404(HIXNYProfile, user=request.user)
    data = OrderedDict()
    data['subject'] = up.subject
    data['patient'] = hp.mrn
    data['cda'] = hp.cda_content
    return JsonResponse(data)


@require_GET
@login_required
def get_cda_raw_test(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp = get_object_or_404(HIXNYProfile, user=request.user)
    return FileResponse(hp.cda_content, content_type='application/xml')
