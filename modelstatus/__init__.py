"""
The modelstatus Python module is an object-based HTTP REST interface to the
Modelstatus service.
"""

import requests
import json
import logging
import dateutil.parser
import datetime
import time

import modelstatus.utils
import modelstatus.exceptions


class BaseResource(modelstatus.utils.SerializeBase):
    required_parameters = []

    def __init__(self, data):
        """
        Initialize a resource with a Python dictionary.
        The constructor takes a data dictionary instead of a strict parameter
        list because we need to iterate over the parameters anyway and assign
        them to the class. It's simpler and DRY-er just to specify them once,
        in the 'required_parameters' list.
        """
        [setattr(self, key, value) for key, value in data.iteritems()]
        self.validate()
        self.initialize()

    def initialize(self):
        """Do variable initialization, overridden by subclasses"""
        pass

    def validate(self):
        """
        Data validation, run before initialize(). May be overridden by
        subclasses. May throw exceptions.
        """
        try:
            for required_parameter in self.required_parameters:
                getattr(self, required_parameter)
        except:
            raise TypeError("Required parameter %s not specified" % required_parameter)


class ModelRun(BaseResource):
    required_parameters = ['id', 'data_provider', 'reference_time', 'created_date', 'version', 'data']
    __serializable__ = ['id', 'data_provider', 'reference_time', 'created_date', 'version', 'data']

    def initialize(self):
        self.reference_time = dateutil.parser.parse(self.reference_time)
        self.created_date = dateutil.parser.parse(self.created_date)
        self.data = [Data(x) for x in self.data]

    def age(self):
        """
        Return model run age, in seconds
        """
        now = datetime.datetime.now()
        now_ts = time.mktime(now.timetuple())
        then_ts = time.mktime(self.reference_time.timetuple())
        return int(now_ts - then_ts)

    def serialize_reference_time(self, value):
        return self._serialize_datetime(value)

    def serialize_created_date(self, value):
        return self._serialize_datetime(value)

    def serialize_data(self, value):
        return [x.serialize() for x in value]

    def __repr__(self):
        return "ModelRun id=%d data_provider=%s reference_time=%s version=%d" % \
            (self.id, self.data_provider, self.reference_time.isoformat(), self.version)


class Data(BaseResource):
    required_parameters = ['id', 'model_run_id', 'format', 'href']
    __serializable__ = ['id', 'model_run_id', 'format', 'href']

    def __repr__(self):
        return "Data id=%d model_run_id=%d format=%s href=%s" % \
            (self.id, self.model_run_id, self.format, self.href)


class BaseCollection(object):
    """
    Base object used to access the REST service.
    """

    def __init__(self, base_url, verify_ssl=True):
        if not issubclass(self.resource, BaseResource):
            raise TypeError('modelstatus.BaseCollection.resource must be inherited from modelstatus.BaseResource')
        self.session = requests.Session()
        self.session.headers.update({'content-type': 'application/json'})
        self.base_url = base_url
        self.verify_ssl = verify_ssl

    def get_collection_url(self):
        """
        Return the URL for the resource collection.
        """
        return "%s/%s" % (self.base_url, self.resource_name)

    def get_resource_url(self, id):
        """
        Given a data set ID, return the web service URL for the data set.
        """
        return "%s/%d" % (self.get_collection_url(), id)

    def get(self, id):
        """
        Requests a single object from the collection.
        Returns an object inheriting from BaseResource.
        """
        data = self._get_raw(id)
        resource = self.resource
        try:
            object_ = resource(data)
        except Exception, e:
            raise modelstatus.exceptions.InvalidResourceException(e)
        logging.info("Downloaded %s" % object_)
        return object_

    def filter(self, **kwargs):
        """
        Makes a query against the entire collection, filtering by specific parameters.
        Returns a list of resources inheriting from BaseResource.
        """
        data = self._filter_raw(kwargs)

        resource = self.resource
        try:
            resources = [resource(x) for x in data]
        except Exception, e:
            raise modelstatus.exceptions.InvalidResourceException(e)
        return resources

    def _make_get_request(self, *args, **kwargs):
        """
        Wrapper for self.session.get with exception handling.
        """
        try:
            response = self.session.get(*args, **kwargs)
        except requests.exceptions.ConnectionError, e:
            raise modelstatus.exceptions.ServiceUnavailableException("Could not connect: %s" % unicode(e))

        if response.status_code >= 500:
            raise modelstatus.exceptions.ServiceUnavailableException(
                "Server returned error code %d for request uri %s " % (response.status_code, response.request.url))
        elif response.status_code >= 400:
            raise modelstatus.exceptions.ClientErrorException(
                "Server returned error code %d for request %s " % (response.status_code, response.request.url))

        return response

    def _get_response_data(self, response):
        """
        Get JSON contents from a response object.
        """
        return response.content

    def _unserialize(self, data):
        """
        Convert JSON encoded data into a dictionary.
        """
        try:
            return json.loads(data)
        except ValueError, e:
            raise modelstatus.exceptions.UnserializeException(e)

    def _filter_raw(self, params):
        """
        Makes a query against the entire collection, filtering by specific parameters.
        Returns a list of dictionaries containing the parsed JSON data.
        """
        url = self.get_collection_url()
        response = self._make_get_request(url, params=params, verify=self.verify_ssl)
        data = self._get_response_data(response)
        return self._unserialize(data)

    def _get_raw(self, id):
        """
        Requests a single object from the collection.
        Returns a dictionary containing the parsed JSON data.
        """
        url = self.get_resource_url(id)
        response = self._make_get_request(url)
        data = self._get_response_data(response)
        return self._unserialize(data)


class ModelRunCollection(BaseCollection):
    """Access the 'model_run' collection of the REST service."""

    resource = ModelRun
    resource_name = 'model_run'

    def latest(self, data_provider):
        """
        Return the latest model run from the specified data_provider, or None
        if no model run was found.
        """
        order_by = [
            'reference_time:desc',
            'version:desc',
        ]
        params = {
            'data_provider': data_provider,
            'order_by': ','.join(order_by),
            'limit': 1,
        }
        results = self.filter(**params)
        return results[0] if len(results) else None


class DataCollection(BaseCollection):
    """Access the 'data' collection of the REST service."""

    resource = Data
    resource_name = 'data'
