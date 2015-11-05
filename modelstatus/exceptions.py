"""
This module contains exception objects used in the Modelstatus client library.
"""


class ModelstatusException(Exception):
    """
    Thrown when there is an error relating to getting data from the REST API.
    """
    pass


class ClientErrorException(ModelstatusException):
    """
    Thrown when the server returns a 4xx error.
    """
    pass


class NotFoundException(ModelstatusException):
    """
    Thrown when the server returns 404.
    """
    pass


class ResourceTypeNotFoundException(NotFoundException):
    """
    Thrown when a resource type can not be found on the server.
    """
    pass


class ResourceNotFoundException(NotFoundException):
    """
    Thrown when a requested resource is not available on the server.
    """
    pass


class ServiceUnavailableException(ModelstatusException):
    """
    Thrown when the server returns a 5xx error.
    """
    pass


class UnserializeException(ModelstatusException):
    """
    Thrown when the data from the REST API could not be decoded.
    """
    pass


class InvalidResourceException(ModelstatusException):
    """
    Thrown when the server returns an invalid resource.
    """
    # FIXME: DEPRECATED
    pass
