
class RaveBaseError(Exception):
    """This is a base error for the Rave API"""
    pass

class InvalidDataError(RaveBaseError):
    """This is called when there is an invalid data passed to the the Rave API"""
    pass

class MissingAuthorizationKeyError(RaveBaseError):
    """There is no authorization key found"""
    pass

class InvalidCardTypeError(RaveBaseError):
    """The card type entered could not be processed"""
    pass

class RaveAPIError(RaveBaseError):
    """The card type entered could not be processed"""
    pass