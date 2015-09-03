import logging
from random import getrandbits

class UserDeniedRequest(Exception):
    pass

class ServiceProviderNotFound(Exception):
    pass

def show_error_page(message):
    error_number = getrandbits(128)
    logging.error("{}: {}".format(error_number, message))
    return """Uh, oh! Somebody messed up! If you could let us know what 
happened and give us this number, that would be great: {}""".format(error_number)
