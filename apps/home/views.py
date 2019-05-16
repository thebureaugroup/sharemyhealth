from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from jwkest.jwt import JWT
from ..hie.models import HIEProfile
from django.contrib import messages
from django.conf import settings

_author_ = "Alan Viars"


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

            if settings.HIE_WORKBENCH_USERNAME:

                if hp.user_accept is False:
                    messages.warning(
                        request, 'Your account is not yet connected to {{settings.APPLICATION_TITLE}} \
                                  personal health information.')

                if hp.cda_content:
                    messages.success(
                        request, 'Your account is already linked to your {{settings.APPLICATION_TITLE}} \
                                  personal health information.')

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
