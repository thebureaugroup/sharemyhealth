import sys
import logging
from datetime import timedelta
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.utils import timezone
from oauth2_provider.decorators import protected_resource
from collections import OrderedDict
from .models import HIEProfile
from ..accounts.models import UserProfile
from . import hixny_requests


logger = logging.getLogger(__name__)


@require_GET
@protected_resource()
def get_patient_fhir_content(request):
    """Only fetch fresh patient FHIR data from HIXNY 
    if the client explicitly requests refresh, or there is not yet any data.

    Otherwise, return whatever data we currently have
    """
    owner = request.resource_owner
    hp, _ = HIEProfile.objects.get_or_create(user=owner)

    if not hp.fhir_content or request.GET.get('refresh', '').lower() == 'true':
        up, _ = UserProfile.objects.get_or_create(user=owner)
        try:
            result = hixny_requests.fetch_patient_data(owner, hp, up)
            if not result.get('error'):
                hp.__dict__.update(**result)
                hp.save()
        except:
            logger.error(
                "Request to fetch_patient_data from Hixny failed for %r: %s"
                % (up, sys.exc_info()[1])
            )
            logger.debug(traceback.format_exc())

    if not hp.fhir_content:
        hie_data = {'error': 'FHIR content is not available'}
    else:
        hie_data = {
            'fhir_data': json.loads(hp.fhir_content or '{}'),
            'updated_at': str(hp.updated_at),
        }

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
