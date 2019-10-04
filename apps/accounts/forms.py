from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class DeleteAccountForm(forms.Form):
    confirm = forms.CharField(max_length=30, label=_('Confirm delete'),
                              help_text=_('Type the word "delete" to confirm.'))

    def clean_confirm(self):
        confirm = self.cleaned_data.get('confirm')
        if confirm.lower() != "delete":
            raise forms.ValidationError(_('Type "delete" to confirm.'))
        return confirm

    required_css_class = 'required'


class AccountSettingsForm(forms.Form):
    username = forms.CharField(
        max_length=30, label=_('User Name'), disabled=True)
    email = forms.CharField(max_length=30, label=_('Email'), disabled=True)
    first_name = forms.CharField(
        max_length=100, label=_('First Name'), disabled=True)
    last_name = forms.CharField(
        max_length=100, label=_('Last Name'), disabled=True)
    mobile_phone_number = forms.CharField(
        max_length=10, required=False, disabled=True)
    organization_name = forms.CharField(max_length=100,
                                        label=_('Organization Name'),
                                        required=False)
    create_applications = forms.BooleanField(initial=False,
                                             required=False)
    required_css_class = 'required'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if email and User.objects.filter(
                    email=email).exclude(email=email).count():
                raise forms.ValidationError(_('This email address is '
                                              'already registered.'))
        return email

    def clean_mobile_phone_number(self):
        mobile_phone_number = self.cleaned_data.get('mobile_phone_number', '')
        mfa_login_mode = self.cleaned_data.get('mfa_login_mode', '')
        if mfa_login_mode == "SMS" and not mobile_phone_number:
            raise forms.ValidationError(
                _('A mobile phone number is required to use SMS-based '
                  'multi-factor authentication'))
        return mobile_phone_number

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(
                username=username).exclude(username=username).count():
            raise forms.ValidationError(_('This username is already taken.'))
        return username
