from functools import update_wrapper
from django.http import HttpResponseForbidden
import logging
from django.utils.translation import ugettext_lazy as _
from jwkest.jwt import JWT

logger = logging.getLogger('sharemyhealth_.%s' % __name__)

_author_ = "Alan Viars"


def check_ial_before_allowing_authorize(func):

    def wrapper(request, *args, **kwargs):

        if request.user.is_authenticated:
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
            if parsed_id_token['ial'] not in ('2', '3'):
                msg = _(
                    "%s %s was defined access due to insufficient identity assurance  level (IAL). Subject=%s"
                    "" %
                    (request.user.first_name, request.user.last_name, parsed_id_token['sub']))
                logger.info(msg)
                response_string = _(
                    """Your identity assurance level (IAL) of 1 is insufficient for this action.""")
                return HttpResponseForbidden(response_string)

        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)


def bind_to_patient(func):

    def wrapper(request, *args, **kwargs):

        if request.user.is_authenticated:
            pass
        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)
