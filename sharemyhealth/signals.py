from oauth2_provider.signals import app_authorized
from django.contrib.auth import get_user_model
from apps.hie.models import HIEProfile


def handle_app_authorized(sender, request, token, **kwargs):
    """This app is now authorized to connect to Hixny data (per the authorize.html form),
    so let's save that fact.
    """
    User = get_user_model()
    user = User.objects.get(id=token.user_id)
    hie_profile, created = HIEProfile.objects.get_or_create(user=user)
    hie_profile.user_accept = True
    hie_profile.save()


app_authorized.connect(handle_app_authorized)
