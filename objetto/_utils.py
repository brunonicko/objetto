import functools

from basicco import caller_module


def auto_caller_module(func):
    """
    Decorate a function that takes a `extra_paths` keyword argument to include the caller module as a path.

    :param func: Function that takes a `extra_paths` keyword argument.
    :return: Decorated function.
    """

    @functools.wraps(func)
    def decorated(*args, **kwargs):
        """Decorated function."""
        extra_paths = kwargs.get("extra_paths", ())
        module = caller_module.caller_module()
        if module not in extra_paths:
            extra_paths += (module,)
        kwargs["extra_paths"] = extra_paths
        return func(*args, **kwargs)

    return decorated
