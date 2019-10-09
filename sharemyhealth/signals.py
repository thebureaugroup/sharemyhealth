import traceback
import logging
from oauth2_provider.signals import app_authorized
from django.contrib.auth import get_user_model
from apps.hie import hixny_requests
from apps.hie.models import HIEProfile
from apps.accounts.models import UserProfile

logger = logging.getLogger(__name__)


def handle_app_authorized(sender, request, token, **kwargs):
    """This app is now authorized to connect to Hixny data (per the authorize.html 
    form), so let's save that fact and get the data.
    """
    User = get_user_model()
    user = User.objects.get(id=token.user_id)
    hie_profile, created = HIEProfile.objects.get_or_create(user=user)
    hie_profile.user_accept = True
    hie_profile.save()

    # let's try getting the user's data now
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    try:
        result = hixny_requests.fetch_patient_data(user, hie_profile, user_profile)
        if not result.get('error'):
            hie_profile.__dict__.update(**result)
            hie_profile.save()
    except Exception:
        logger.error(
            "Request to fetch_patient_data from Hixny failed for %r\n%s"
            % (user_profile, traceback.format_exc())
        )


app_authorized.connect(handle_app_authorized)
