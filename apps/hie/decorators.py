from functools import update_wrapper


def bind_to_patient(func):

    def wrapper(request, *args, **kwargs):

        if request.user.is_authenticated:
            pass

        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)
