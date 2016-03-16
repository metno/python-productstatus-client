"""
This module contains exception objects used in the Productstatus client library.
"""


class ProductstatusException(Exception):
    """
    Thrown when there is an error relating to getting data from the REST API.
    """
    pass


class InvalidFilterDataException(ProductstatusException):
    """
    Thrown when filter data for query sets are invalid.
    """
    pass


class InvalidFilterDataException(ProductstatusException):
    """
    Thrown when filter data for query sets are invalid.
    """
    pass


class ClientErrorException(ProductstatusException):
    """
    Thrown when the server returns a 4xx error.
    """
    pass


class UnauthorizedException(ClientErrorException):
    """
    Thrown when the server returns 401.
    """
    pass


class NotFoundException(ClientErrorException):
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


class ServiceUnavailableException(ProductstatusException):
    """
    Thrown when the server returns a 5xx error.
    """
    pass


class UnserializeException(ProductstatusException):
    """
    Thrown when the data from the REST API could not be decoded.
    """
    pass


class InvalidResourceException(ProductstatusException):
    """
    Thrown when the server returns an invalid resource.
    """
    # FIXME: DEPRECATED
    pass


class EventException(ProductstatusException):
    """
    Parent class for all exceptions related to Productstatus events.
    """
    pass


class EventTimeoutException(EventException):
    """!
    @brief Thrown when an event is not available on the Kafka socket.
    """
    pass
