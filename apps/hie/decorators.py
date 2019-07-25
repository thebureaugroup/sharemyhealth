from .models import UserProfile
from functools import update_wrapper
from django.conf import settings


def bind_to_patient(func):

    def wrapper(request, *args, **kwargs):
        print("HERE")
        if request.user.is_authenticated:
            print("ddd")  

        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)