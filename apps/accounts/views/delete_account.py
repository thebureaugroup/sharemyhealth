import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import DeleteAccountForm
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
logger = logging.getLogger('sharemyhealth_.%s' % __name__)

__author__ = "Alan Viars"


@login_required
def account_delete(request):

    name = _('Delete Account')
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            logger.info("$s deleted account.", request.user)
            request.user.delete()
            logger.info("%s logged out.", request.user)
            logout(request)
            messages.success(request,
                             'Your account was deleted.')
            return HttpResponseRedirect(reverse('home'))
        else:
            # the form had errors
            return render(request,
                          'generic/bootstrapform.html',
                          {'form': form, 'name': name})

    # this is an HTTP GET
    return render(request, 'generic/bootstrapform.html',
                  {'name': name, 'form': DeleteAccountForm()})
