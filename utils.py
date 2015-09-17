
from functools import wraps

def log_io(printer):
    """ Returns a decorator that logs function IO

    The returned decorator displays the arguments and return value of the
    decorated function using the "printer", which is e.g. `logger.debug`.

    >>> import logging
    >>> log = logging.getLogger(__name__)
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> @log_io(log.debug)
    ... def adder(a1, a2):
    ...     return a1 + a2
    ...
    >>> adder(3, 4)
    7

    :param printer: logging.Logger.{debug, info, warning, etc.}
    :return: (decorator)
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            printer("Function called: {!r}".format(f))
            printer("args: {!r}".format(args))
            printer("kwargs: {!r}".format(kwargs))
            ret = f(*args, **kwargs)
            printer("Returned: {!r}".format(ret))
            return ret
        return decorated
    return decorator