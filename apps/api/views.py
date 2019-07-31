from collections import OrderedDict
# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import (
    renderers,
)
from rest_framework_xml.renderers import XMLRenderer
import os
from oauth2_provider.decorators import protected_resource
from django.views.decorators.http import require_GET
from django.contrib.sessions.models import Session
import logging
from django.http import JsonResponse

logger = logging.getLogger('sharemyhealth_.%s' % __name__)

class CDAExample(APIView):

    # authentication_classes = (authentication.TokenAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,
                        renderers.JSONRenderer, XMLRenderer, )

    def get_data(self):
        data = OrderedDict()
        data["sub"] = "12345678912345"
        data["patient"] = "984848940"
        with open(os.path.join(os.path.dirname(__file__), "sample-cda.xml")) as f:
            ccda = f.read()
            data["cda"] = ccda
        return data

    def get(self, request, format=None):
        return Response(self.get_data())


@require_GET
@protected_resource()
def logout_user(request):
    # A remote API call for logging out the user.
    # It works by expiring all sessions for a user.
    user = request.resource_owner
    delete_all_sessions_for_user(user)
    data = {"status": "ok",
            "message": "%s sessions removed. Remote logout." % (user)}
    logger.info("$s logged out remotely.", user)
    return JsonResponse(data)


def delete_all_sessions_for_user(user):
    user_sessions = []
    all_sessions = Session.objects.all()
    for session in all_sessions:
        session_data = session.get_decoded()
        if str(user.pk) == str(session_data.get('_auth_user_id')):
            user_sessions.append(session.pk)
    Session.objects.filter(pk__in=user_sessions).delete()
    return user_sessions