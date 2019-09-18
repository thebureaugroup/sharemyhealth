#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from ..models import Crosswalk
from jwkest.jwt import JWT

__author__ = "Alan Viars"


def set_crosswalk_with_id_token(backend, user, response, *args, **kwargs):
    if backend.name == 'verifymyidentity-openidconnect':

        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            payload = parsed_id_token.payload()

            if 'document' in payload:
                for doc in payload['document']:
                    # Does it already exist?
                    cw, g_o_c = Crosswalk.objects.get_or_create(user=user,
                                                                user_identifier=doc[
                                                                    'num'],
                                                                user_id_type=doc['type'])

                    cw.fhir_source = doc['uri']
                    if doc['type'] == "PATIENT_ID_FHIR":
                        cw.fhir_patient_id = doc['num']
                    cw.save()
