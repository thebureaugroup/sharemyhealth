from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from jwkest.jwt import JWT
from ..hie.models import HIEProfile
from ..hie.hixny_requests import acquire_access_token, consumer_directive, get_clinical_document
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponseRedirect, FileResponse
from django.urls import reverse

_author_ = "Alan Viars"


@login_required
def fetch_cda(request):
    hp, g_o_c = HIEProfile.objects.get_or_create(user=request.user)
    # print(hp)

    if not hp.mrn:
        msg = _(
            "Your identity is not yet bound to a resource. Try connecting with OAuth2 using the Test client.")
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse('authenticated_home'))
    access_token = acquire_access_token()
    # print(access_token)
    result = consumer_directive(
        access_token['access_token'], hp, request.user.userprofile)
    result = get_clinical_document(access_token['access_token'], hp)
    # print(result)
    return FileResponse(result['response_body'],
                        content_type='application/xml')


@login_required
def id_token_payload_json(request):

    try:
        vmi = request.user.social_auth.filter(
            provider='verifymyidentity-openidconnect')[0]
        extra_data = vmi.extra_data
        if 'id_token' in vmi.extra_data.keys():
            id_token = extra_data.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            parsed_id_token = parsed_id_token.payload()
    except Exception:
        id_token = "No ID token."
        parsed_id_token = {'sub': '', 'ial': '1',
                           "note": "No ID token for this user"}
    return JsonResponse(parsed_id_token)


def authenticated_home(request):
    name = _('Authenticated Home')
    if request.user.is_authenticated:

        # Get the ID Token and parse it.
        try:
            vmi = request.user.social_auth.filter(
                provider='verifymyidentity-openidconnect')[0]
            extra_data = vmi.extra_data
            if 'id_token' in vmi.extra_data.keys():
                id_token = extra_data.get('id_token')
                parsed_id_token = JWT().unpack(id_token)
                parsed_id_token = parsed_id_token.payload()

        except Exception:
            id_token = "No ID token."
            parsed_id_token = {'sub': '', 'ial': '1'}

        hp, g_o_c = HIEProfile.objects.get_or_create(
            user=request.user)

        if parsed_id_token.get('ial') not in ('2', '3'):
            # redirect to get verified
            messages.warning(request, 'Your identity has not been verified. \
                             This must be completed prior to access to personal health information.')

        try:
            profile = request.user.userprofile
        except Exception:
            profile = None

        # this is a GET
        context = {'name': name, 'profile': profile, 'hp': hp,
                   'id_token': id_token,
                   'id_token_payload': parsed_id_token}

        template = 'authenticated-home.html'
    else:
        name = ('home')
        context = {'name': name}
        template = 'index.html'
    return render(request, template, context)
