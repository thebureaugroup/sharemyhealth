from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

# Copyright Videntity Systems Inc.


__author__ = "Alan Viars"


class Crosswalk(models.Model):
    """
    User to FHIR patient ID crosswalk
    """

    user = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT, null=True)
    fhir_source = models.CharField(default=settings.DEFAULT_FHIR_SERVER,
                                   blank=True, max_length=512,
                                   verbose_name=_('The backend FHIR server to proxy'))
    use_client_credentials = models.BooleanField(blank=True, default=False,
                                                 help_text="""When checked, OAuth2 client credentials to
                                             access the FHIR source using values in settings.py""")

    fhir_patient_id = models.CharField(max_length=80,
                                       blank=True, default="", unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    user_identifier = models.CharField(max_length=120, blank=True,
                                       default="")
    user_id_type = models.CharField(max_length=3,
                                    default="CIN", blank=True,
                                    choices=(("CIN", "CIN"),))
    user_id_hash = models.CharField(max_length=64,
                                    blank=True,
                                    default="",
                                    verbose_name=_("PBKDF2 of User ID"))
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.user_identifier

    def patient_fhir_url(self):
        fhir_endpoint = "%sPatient/%s" % (self.fhir_source,
                                          self.fhir_patient_id)
        return fhir_endpoint

    class Meta:
        unique_together = (("user", "user_identifier", "user_id_type"),)
