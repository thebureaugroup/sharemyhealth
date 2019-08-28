import re
from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .models import HIEProfile
from ..accounts.models import UserProfile


def write_key_to_filepath(filepath, env_to_write):
    # try and open the local file. Create it from an env var if it doesn't exist.
    # return the filepath
    try:
        f = open(filepath, 'r')
        f.close()
    except FileNotFoundError:
        f = open(filepath, 'w')
        f.write(env_to_write)
        f.close()
    return filepath


NAMESPACES = {
    'hl7': "urn:hl7-org:v3",
    'enrollment': "http://www.intersystems.com/hs/portal/enrollment",
}


def fetch_patient_data(user, hie_profile=None, user_profile=None):
    """do what we need to do to fetch patient data from HIXNY, if possible, for the given user.
    returns values that can be used to update the user's HIEProfile
    """
    result = {'responses': []}

    if hie_profile is None:
        hie_profile, created = HIEProfile.objects.get(user=user)
    if user_profile is None:
        user_profile, created = UserProfile.objects.get(user=user)

    if hie_profile.flag_dont_connect:
        result['cda_content'] = hie_profile.cda_content
        result['fhir_content'] = hie_profile.fhir_content
    else:
        # acquire an access token from the HIXNY server
        auth_response = acquire_access_token()
        if auth_response['error_message'] is not None:
            result['error'] = auth_response['error_message']
            return result
        access_token = auth_response['access_token']

        # if the member hasn't been enrolled (no HIEProfile.mrn), try to enroll
        if not hie_profile.mrn:
            # try to find the member
            search_data = patient_search(access_token, user_profile)
            if 'response_body' in search_data:
                result['responses'].append(search_data['response_body'])

            if search_data.get('mrn'):
                # member found, already has portal account
                hie_profile.mrn = search_data['mrn']
                hie_profile.save()

            elif not (
                search_data.get('error')
                or search_data.get('status') == 'ERROR'
                and search_data.get('notice')
            ):
                # member found
                hie_profile.terms_accepted = search_data.get('terms_accepted')
                hie_profile.terms_string = search_data.get('terms_string')
                hie_profile.stageuser_password = search_data.get(
                    'stageuser_password')
                hie_profile.stageuser_token = search_data.get(
                    'stageuser_token')
                hie_profile.save()

                # try to stage/activate the member
                activated_member_data = activate_staged_user(
                    access_token, hie_profile, user_profile
                )
                print('activated_member_data:', activated_member_data)
                if 'response_body' in activated_member_data:
                    result['responses'].append(
                        activated_member_data['response_body'])

                if (
                    activated_member_data.get('mrn')
                    and activated_member_data['status'] == 'success'
                ):
                    hie_profile.mrn = activated_member_data['mrn']
                    hie_profile.save()

                print(
                    {k: v for k, v in hie_profile.__dict__.items() if k[0] != '_'})

        # if the consumer directive checks out, get the clinical data and store
        # it
        directive = consumer_directive(access_token, hie_profile, user_profile)
        if 'response_body' in directive:
            result['responses'].append(directive['response_body'])

        if directive['status'] == "OK":
            document_data = get_clinical_document(access_token, hie_profile)
            if 'response_body' in document_data:
                result['responses'].append(document_data['response_body'])

            result['cda_content'] = document_data['cda_content']
            result['fhir_content'] = document_data['fhir_content']
        else:
            result['error'] = "Clinical data could not be loaded."
            if settings.DEBUG and directive.get('error'):
                result['error'] += " (%s)" % directive['error'] or ''

    return result


def acquire_access_token():
    """establish a connection to the HIXNY service;
    returns JSON containing an access token on successful connection
    """
    data = {
        "grant_type": "password",
        "username": settings.HIE_WORKBENCH_USERNAME,
        "password": settings.HIE_WORKBENCH_PASSWORD,
        "scope": "/PHRREGISTER",
    }
    response = requests.post(
        settings.HIE_TOKEN_API_URI,
        cert=(write_key_to_filepath(settings.HIE_CLIENT_CERT_FILEPATH, settings.HIE_CLIENT_CERT),
              write_key_to_filepath(settings.HIE_CLIENT_PRIVATE_KEY_FILEPATH, settings.HIE_CLIENT_PRIVATE_KEY)),
        data=data,
        verify=False,
        auth=HTTPBasicAuth('password-client',
                           settings.HIE_BASIC_AUTH_PASSWORD),
    )
    response_json = response.json()
    if 'access_token' not in response_json:
        access_token = None
        error_message = _(
            "We're sorry. We could not connect to HIE. Please try again later."
        )
        if settings.DEBUG is True:
            error_message += " DATA=%s response=%s TOKEN_URI=%s BASIC_AUTH=%s" % (
                data,
                response_json,
                settings.HIE_TOKEN_API_URI,
                settings.HIE_BASIC_AUTH_PASSWORD,
            )
    else:
        access_token = response_json['access_token']
        error_message = None

    return {'access_token': access_token, 'error_message': error_message}


def patient_search(access_token, user_profile):
    """search for a patient with the given profile; if found, return """
    patient_search_xml = """
       <PatientSearchPayLoad>
            <PatGender>%s</PatGender>
            <PatDOB>%s</PatDOB>
            <PatFamilyName>%s</PatFamilyName>
            <PatGivenName>%s</PatGivenName>
            <PatMiddleName></PatMiddleName>
            <PatPrefix></PatPrefix>
            <PatSuffix></PatSuffix>
            <PatAddrStreetOne></PatAddrStreetOne>
            <PatAddrStreetTwo></PatAddrStreetTwo>
            <PatAddrCity></PatAddrCity>
            <PatAddrZip></PatAddrZip>
            <PatAddrState></PatAddrState>
            <PatSSN></PatSSN>
            <PatHomePhone></PatHomePhone>
            <PatEmail></PatEmail>
            <WorkBenchUserName>%s</WorkBenchUserName>
            <ConsentToShareData>1</ConsentToShareData>
        </PatientSearchPayLoad>
        """ % (
        user_profile.gender_intersystems,
        user_profile.birthdate_intersystems,
        user_profile.user.last_name,
        user_profile.user.first_name,
        settings.HIE_WORKBENCH_USERNAME,
    )
    # print(patient_search_xml)

    response = requests.post(
        settings.HIE_PHRREGISTER_API_URI,
        cert=(write_key_to_filepath(settings.HIE_CLIENT_CERT_FILEPATH, settings.HIE_CLIENT_CERT),
              write_key_to_filepath(settings.HIE_CLIENT_PRIVATE_KEY_FILEPATH, settings.HIE_CLIENT_PRIVATE_KEY)),
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token),
        },
        data=patient_search_xml,
    )

    response_xml = etree.XML(response.content)
    result = {"response_body": etree.tounicode(
        response_xml, pretty_print=True)}
    # print(result['response_body'])

    for element in response_xml:
        if element.tag == "{%(hl7)s}Notice" % NAMESPACES:
            result['error'] = element.text
        for e in element.getchildren():
            if e.tag == "{%(hl7)s}Status" % NAMESPACES:
                result['status'] = e.text
            if e.tag == "{%(hl7)s}Notice" % NAMESPACES:
                result['notice'] = e.text
                if "ERROR #5001" in result['notice']:
                    match_data = re.search(
                        r'MRN[:=] ?([0-9]+)\b', result['notice'])
                    if match_data:
                        result['mrn'] = match_data.group(1)
            if e.tag == "{%(hl7)s}TERMSACCEPTED" % NAMESPACES:
                result['terms_accepted'] = e.text
            if e.tag == "{%(enrollment)s}TermsString" % NAMESPACES:
                # the content of TermsString is html
                e.tag = 'TermsString'  # get rid of namespaces
                terms_string = ''.join(
                    [etree.tounicode(ch, method='xml') for ch in e])
                result['terms_string'] = terms_string
            if e.tag == "{%(hl7)s}StageUserPassword" % NAMESPACES:
                result['stageuser_password'] = e.text
            if e.tag == "{%(hl7)s}StageUserToken" % NAMESPACES:
                result['stageuser_token'] = e.text

    return result


def activate_staged_user(access_token, hie_profile, user_profile):
    """try to activate the member with HIXNY;
    if successful, returns MRN
    """
    activate_xml = """
        <ACTIVATESTAGEDUSERPAYLOAD>
            <DOB>%s</DOB>
            <TOKEN>%s</TOKEN>
            <PASSWORD>%s</PASSWORD>
            <TERMSACCEPTED>%d</TERMSACCEPTED>
        </ACTIVATESTAGEDUSERPAYLOAD>
        """ % (
        user_profile.birthdate_intersystems,
        hie_profile.stageuser_token,
        hie_profile.stageuser_password,
        hie_profile.consent_to_share_data,
    )
    # print(activate_xml)

    response = requests.post(
        settings.HIE_ACTIVATESTAGEDUSER_API_URI,
        cert=(write_key_to_filepath(settings.HIE_CLIENT_CERT_FILEPATH, settings.HIE_CLIENT_CERT),
              write_key_to_filepath(settings.HIE_CLIENT_PRIVATE_KEY_FILEPATH, settings.HIE_CLIENT_PRIVATE_KEY)),
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token),
        },
        data=activate_xml,
    )

    response_content = response.content.decode('utf-8')
    response_xml = etree.XML(response.content)

    result = {"response_body": etree.tounicode(
        response_xml, pretty_print=True)}
    # print(result['response_body'])

    mrn_elements = response_xml.xpath(
        "//hl7:ActivatedUserMrn", namespaces=NAMESPACES)
    mrn_match = re.search(r"ActivatedUserMrn>(\d+)<", response_content)

    if len(mrn_elements) > 0:
        mrn_element = mrn_elements[0]
        # print('mrn_element =', etree.tounicode(mrn_element))
        result.update(
            status='success',
            mrn=etree.tounicode(mrn_element, method='text',
                                with_tail=False).strip(),
        )
    elif mrn_match is not None:
        # print('mrn_match =', mrn_match)
        result.update(status='success', mrn=mrn_match.group(1))
    else:
        result.update(
            status='failure', mrn=None, error='Could not activate staged user.'
        )

    return result


def consumer_directive(access_token, hie_profile, user_profile):
    """post to the consumer directive API to determine the member's consumer directive;
    returns data containing the status and any notice.
    """
    if not hie_profile.consent_to_share_data:
        result = {
            'status': 'ERROR',
            'notice': 'Member has not consented to share data, cannot submit consumer directive.',
        }
    elif not hie_profile.mrn:
        result = {
            'status': 'ERROR',
            'notice': 'Member MRN not set, cannot submit consumer directive.',
        }
    else:
        consumer_directive_xml = """
            <CONSUMERDIRECTIVEPAYLOAD>
                <MRN>%s</MRN>
                <DOB>%s</DOB>
                <DATAREQUESTOR>%s</DATAREQUESTOR>
                <CONSENTTOSHAREDATA>%d</CONSENTTOSHAREDATA>
            </CONSUMERDIRECTIVEPAYLOAD>
            """ % (
            hie_profile.mrn,
            user_profile.birthdate_intersystems,
            hie_profile.data_requestor,
            hie_profile.consent_to_share_data,
        )
        # print(consumer_directive_xml)

        response = requests.post(
            settings.HIE_CONSUMERDIRECTIVE_API_URI,
            cert=(write_key_to_filepath(settings.HIE_CLIENT_CERT_FILEPATH, settings.HIE_CLIENT_CERT),
                  write_key_to_filepath(settings.HIE_CLIENT_PRIVATE_KEY_FILEPATH, settings.HIE_CLIENT_PRIVATE_KEY)),
            verify=False,
            headers={
                'Content-Type': 'application/xml',
                'Authorization': "Bearer %s" % (access_token),
            },
            data=consumer_directive_xml,
        )
        response_xml = etree.XML(response.content)
        result = {"response_body": etree.tounicode(
            response_xml, pretty_print=True)}
        # print(result['response_body'])

        result.update(
            status=''.join(
                response_xml.xpath("hl7:Status/text()", namespaces=NAMESPACES)
            ),
            notice=''.join(
                response_xml.xpath("hl7:Notice/text()", namespaces=NAMESPACES)
            ),
        )
        if result['status'] == 'ERROR':
            result['error'] = result['notice']

    return result


def get_clinical_document(access_token, hie_profile):
    """get member's clinical data from HIXNY (CDA XML), convert to FHIR (JSON), return both.
    """
    request_xml = """
        <GETDOCUMENTPAYLOAD>
            <MRN>%s</MRN>
            <DATAREQUESTOR>%s</DATAREQUESTOR>
        </GETDOCUMENTPAYLOAD>
        """ % (
        hie_profile.mrn,
        hie_profile.data_requestor,
    )
    # print(request_xml)

    response = requests.post(
        settings.HIE_GETDOCUMENT_API_URI,
        cert=(write_key_to_filepath(settings.HIE_CLIENT_CERT_FILEPATH, settings.HIE_CLIENT_CERT),
              write_key_to_filepath(settings.HIE_CLIENT_PRIVATE_KEY_FILEPATH, settings.HIE_CLIENT_PRIVATE_KEY)),
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token),
        },
        data=request_xml,
    )
    response_xml = etree.XML(response.content)

    result = {"response_body": etree.tounicode(
        response_xml, pretty_print=True)}

    cda_element = response_xml.find("{%(hl7)s}ClinicalDocument" % NAMESPACES)
    if cda_element is not None:
        cda_content = etree.tounicode(cda_element)
        fhir_content = cda2fhir(cda_content).decode('utf-8')
        result.update(cda_content=cda_content, fhir_content=fhir_content)
    else:
        result.update(cda_content='', fhir_content='')

    return result


def cda2fhir(cda_content):
    """use the CDA2FHIR service to convert CDA XML to FHIR JSON"""
    response = requests.post(
        settings.CDA2FHIR_SERVICE_URL,
        data=cda_content,
        headers={'Content-Type': 'application/xml'},
    )
    fhir_content = response.content
    return fhir_content
