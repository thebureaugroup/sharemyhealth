# import logging #TODO
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..accounts.models import UserProfile
from .models import HIEProfile
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from . import hixny_requests


@login_required
def cda2fhir_patient_data(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp, g_o_c = HIEProfile.objects.get_or_create(user=request.user)

    hp.fhir_content = hixny_requests.cda2fhir(hp.cda_content)
    hp.save()

    messages.success(request, "CDA to FHIR.")
    return HttpResponseRedirect(reverse('home'))


@login_required
def refresh_patient_data(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp, g_o_c = HIEProfile.objects.get_or_create(user=request.user)

    # get an access token for this session
    auth_response = hixny_requests.acquire_access_token()
    if auth_response['error_message'] is not None:
        messages.error(request, auth_response['error_message'])
        return HttpResponseRedirect(reverse('home'))
    access_token = auth_response['access_token']

    # if the consumer directive checks out, get the clinical data and store it
    directive = hixny_requests.consumer_directive(access_token, hp, up)
    if directive['status'] == "OK" and directive['notice'] in (
            "Document has been prepared.",
            "Document already exists.",
    ):
        document_data = hixny_requests.get_clinical_document(access_token, hp)
        hp.cda_content = document_data['cda_content']
        hp.fhir_content = document_data['fhir_content']
        hp.save()
        messages.success(request, "Clinical data refreshed.")
    else:
        warning = "Clinical data could not be loaded."
        if settings.DEBUG:
            warning += " %r" % directive
        messages.warning(request, warning)

    return HttpResponseRedirect(reverse('home'))


@login_required
def get_authorization(request):
    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp, g_o_c = HIEProfile.objects.get_or_create(user=request.user)

    # get an access token for this session
    auth_response = hixny_requests.acquire_access_token()
    if auth_response['error_message'] is not None:
        messages.error(request, auth_response['error_message'])
        return HttpResponseRedirect(reverse('home'))
    access_token = auth_response['access_token']

    search_data = hixny_requests.patient_search_enroll(access_token, up)
    if search_data.get('error'):
        error_message = "HIE Responded: %(error)s" % search_data
        messages.error(request, error_message)
        return HttpResponseRedirect(reverse('home'))
    elif search_data.get('status') == 'ERROR' and search_data.get('notice'):
        error_message = "HIE Responded: %(notice)s" % search_data
        messages.error(request, error_message)
        return HttpResponseRedirect(reverse('home'))
    else:
        # messages.info(request, "status: %(status)s, notice: %(notice)s" % search_data)
        hp.terms_accepted = search_data.get('terms_accepted')
        hp.terms_string = search_data.get('terms_string')
        hp.stageuser_password = search_data.get('stageuser_password')
        hp.stageuser_token = search_data.get('stageuser_token')
        hp.save()

    # Send the terms accepted response...
    context = {"hp": hp}
    return render(request, 'hixny-user-agreement.html', context)


@login_required
def approve_authorization(request):

    up, g_o_c = UserProfile.objects.get_or_create(user=request.user)
    hp, g_o_c = HIEProfile.objects.get_or_create(user=request.user)

    # get an access token for this session
    auth_response = hixny_requests.acquire_access_token()
    if auth_response['error_message'] is not None:
        messages.error(request, auth_response['error_message'])
        return HttpResponseRedirect(reverse('home'))
    access_token = auth_response['access_token']

    # activate user
    staged_user_data = hixny_requests.activate_staged_user(access_token, hp, up)
    if staged_user_data['status'] == 'success':
        hp.mrn = staged_user_data['mrn']
        hp.save()

    # if the consumer directive checks out, get the clinical data and store it
    directive = hixny_requests.consumer_directive(access_token, hp, up)
    if directive['status'] == "OK" and directive['notice'] in (
            "Document has been prepared.",
            "Document already exists.",
    ):
        document_data = hixny_requests.get_clinical_document(access_token, hp)
        hp.cda_content = document_data['cda_content']
        hp.fhir_content = document_data['fhir_content']
        hp.save()
        messages.success(request, "Clinical data stored.")
    else:
        messages.warning(request, "Clinical data unchanged. %r" % (directive))

    # Send the terms accepted response...
    context = {}
    return render(request, 'hixny-approve-agreement.html', context)
