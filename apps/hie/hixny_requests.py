from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .models import HIEProfile
from ..accounts.models import UserProfile

NAMESPACES = {
    'hl7': 'urn:hl7-org:v3',
}


def acquire_access_token():
    """establish a connection to the hixny service;
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
        data=data,
        verify=False,
        auth=HTTPBasicAuth('password-client', settings.HIE_BASIC_AUTH_PASSWORD),
    )
    response_json = response.json()
    if 'access_token' not in response_json:
        access_token = None
        error_message = _("We're sorry. We could not connect to HIE. Please try again later.")
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

    return {
        'access_token': access_token,
        'error_message': error_message,
    }


def patient_search_enroll(access_token, user_profile):
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
        </PatientSearchPayLoad>
        """ % (
        user_profile.gender_intersystems,
        user_profile.birthdate_intersystems,
        user_profile.user.last_name,
        user_profile.user.first_name,
        settings.HIE_WORKBENCH_USERNAME,
    )
    response = requests.post(
        settings.HIE_PHRREGISTER_API_URI,
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token)
        },
        data=patient_search_xml)

    response_xml = etree.XML(response.content)
    print(etree.tounicode(response_xml, pretty_print=True))

    result = {}
    for element in response_xml:
        if element.tag == "{urn:hl7-org:v3}Notice":
            result['error'] = element.text
        for e in element.getchildren():
            if e.tag == "{urn:hl7-org:v3}Status":
                result['status'] = e.text
            if e.tag == "{urn:hl7-org:v3}Notice":
                result['notice'] = e.text
            if e.tag == "{urn:hl7-org:v3}TERMSACCEPTED":
                result['terms_accepted'] = e.text
            if e.tag == "{http://www.intersystems.com/hs/portal/enrollment}TermsString":
                result['terms_string'] = e.text
            if e.tag == "{urn:hl7-org:v3}StageUserPassword":
                result['stageuser_password'] = e.text
            if e.tag == "{urn:hl7-org:v3}StageUserToken":
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
            <TERMSACCEPTED>%s</TERMSACCEPTED>
        </ACTIVATESTAGEDUSERPAYLOAD>
        """ % (
        user_profile.birthdate_intersystems,
        hie_profile.stageuser_token,
        hie_profile.stageuser_password,
        hie_profile.consent_to_share_data,
    )

    response = requests.post(
        settings.HIE_ACTIVATESTAGEDUSER_API_URI,
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token)
        },
        data=activate_xml)

    response_xml = etree.XML(response.content)
    print(etree.tounicode(response_xml, pretty_print=True))

    mrn_element = response_xml.find("{%(hl7)s}ActivatedUserMrn" % NAMESPACES)
    if mrn_element and mrn_element.text:
        result = {'status': 'success', 'mrn': mrn_element.text}
    else:
        result = {'status': 'failure', 'mrn': None}

    return result


def consumer_directive(access_token, hie_profile, user_profile):
    """post to the consumer directive API to determine the given member's consumer directive;
    returns data containing the status and any notice.
    """
    consumer_directive_xml = """
        <CONSUMERDIRECTIVEPAYLOAD>
            <MRN>%s</MRN>
            <DOB>%s</DOB>
            <DATAREQUESTOR>%s</DATAREQUESTOR>
            <CONSENTTOSHAREDATA>%s</CONSENTTOSHAREDATA>
        </CONSUMERDIRECTIVEPAYLOAD>
        """ % (
        hie_profile.mrn,
        user_profile.birthdate_intersystems,
        hie_profile.data_requestor,
        hie_profile.consent_to_share_data,
    )
    response = requests.post(
        settings.HIE_CONSUMERDIRECTIVE_API_URI,
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token)
        },
        data=consumer_directive_xml,
    )
    response_xml = etree.XML(response.content)
    print(etree.tounicode(response_xml, pretty_print=True))

    return {
        'status': ''.join(
            response_xml.xpath("hl7:Status/text()", namespaces=NAMESPACES)),
        'notice': ''.join(
            response_xml.xpath("hl7:Notice/text()", namespaces=NAMESPACES)),
    }


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
    response = requests.post(
        settings.HIE_GETDOCUMENT_API_URI,
        verify=False,
        headers={
            'Content-Type': 'application/xml',
            'Authorization': "Bearer %s" % (access_token)
        },
        data=request_xml,
    )
    response_xml = etree.XML(response.content)
    cda_element = response_xml.find("{%(hl7)s}ClinicalDocument" % NAMESPACES)
    if cda_element is not None:
        cda_content = etree.tounicode(cda_element)
        fhir_content = cda2fhir(cda_content).decode('utf-8')
        result = {
            'cda_content': cda_content,
            'fhir_content': fhir_content,
        }
    else:
        result = {
            'cda_content': None,
            'fhir_content': None,
        }

    return result


def cda2fhir(cda_content):
    """use the CDA2FHIR service to convert CDA XML to FHIR JSON"""
    response = requests.post(
        settings.CDA2FHIR_SERVICE_URL,
        data=cda_content,
        headers={'Content-Type': 'application/xml'})
    fhir_content = response.content
    return fhir_content


def fetch_patient_data(user, hie_profile=None, user_profile=None):
    """do what we need to do to fetch patient data from HIXNY, if possible, for the given user.
    returns values that can be used to update the user's HIEProfile
    """
    result = {}

    # acquire an access token from the HIXNY server
    auth_response = acquire_access_token()
    if auth_response['error_message'] is not None:
        result['error'] = auth_response['error_message']
        return result
    access_token = auth_response['access_token']

    if hie_profile is None:
        hie_profile, created = HIEProfile.objects.get(user=user)
    if user_profile is None:
        user_profile, created = UserProfile.objects.get(user=user)

    # if the consumer directive checks out, get the clinical data and store it
    directive = consumer_directive(access_token, hie_profile, user_profile)
    if directive['status'] == "OK" and directive['notice'] in (
            "Document has been prepared.",
            "Document already exists.",
    ):
        document_data = get_clinical_document(access_token, hie_profile)
        result['cda_content'] = document_data['cda_content']
        result['fhir_content'] = document_data['fhir_content']
    else:
        result['error'] = "Clinical data could not be loaded."
        if settings.DEBUG:
            result['error'] += " %r" % directive
        return result

    return result
