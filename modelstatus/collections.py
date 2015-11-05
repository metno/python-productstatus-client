import requests
import json

import modelstatus.utils
import modelstatus.exceptions
import modelstatus.resources


class BaseCollection(object):
    """
    Base object used to access the REST service.
    """

    def __init__(self, base_url, verify_ssl=True, username=None, password=None):
        if not issubclass(self.resource, modelstatus.resources.BaseResource):
            raise TypeError('modelstatus.BaseCollection.resource must be inherited from modelstatus.BaseResource')
        self.auth = (username, password)
        self.base_url = base_url.strip('/') + '/api/v1/'
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = self.verify_ssl
        self.session.headers.update({'content-type': 'application/json'})

    def get_collection_url(self):
        """
        Return the URL for the resource collection.
        """
        return modelstatus.utils.build_url(self.base_url, self.resource_name)

    def get_resource_url(self, id):
        """
        Given a data set ID, return the web service URL for the data set.
        """
        return modelstatus.utils.build_url(self.get_collection_url(), id)

    def get(self, id):
        """
        Requests a single object from the collection.
        Returns an object inheriting from BaseResource.
        """
        resource = self._get_raw(id)
        return self._object_from_dictionary(resource)

    def post(self, data):
        """
        Post a new object to the collection.
        Returns an object inheriting from BaseResource.
        """
        resource = self._post_raw(data)
        return self._object_from_dictionary(resource)

    def filter(self, **kwargs):
        """
        Makes a query against the entire collection, filtering by specific parameters.
        Returns a list of resources inheriting from BaseResource.
        """
        data = self._filter_raw(kwargs)
        resources = [self._object_from_dictionary(x) for x in data]
        return resources

    def _object_from_dictionary(self, dictionary):
        resource = self.resource
        try:
            object_ = resource(dictionary)
        except Exception, e:
            raise modelstatus.exceptions.InvalidResourceException(e)
        return object_

    def _raise_response_exceptions(self, response):
        if response.status_code < 400:
            return
        if response.status_code >= 500:
            exception = modelstatus.exceptions.ServiceUnavailableException
        elif response.status_code == 404:
            exception = modelstatus.exceptions.NotFoundException
        else:
            exception = modelstatus.exceptions.ClientErrorException
        raise exception(response.text)

    def _do_request(self, method, *args, **kwargs):
        """
        Wrapper for self.session.{get,post,patch,put,delete} with exception handling
        """
        try:
            func = getattr(self.session, method)
            response = func(*args, **kwargs)
        except requests.exceptions.ConnectionError, e:
            raise modelstatus.exceptions.ServiceUnavailableException("Could not connect: %s" % unicode(e))

        self._raise_response_exceptions(response)
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
        response = self._do_request('get', url, params=params, verify=self.verify_ssl)
        data = self._get_response_data(response)
        return self._unserialize(data)

    def _get_raw(self, id):
        """
        Requests a single object from the collection.
        Returns a dictionary containing the parsed JSON data.
        """
        url = self.get_resource_url(id)
        response = self._do_request('get', url)
        data = self._get_response_data(response)
        print data
        return self._unserialize(data)

    def _post_raw(self, data):
        """
        Post a new object to the collection.
        Returns a dictionary containing the result object.
        """
        url = self.get_collection_url()
        payload = json.dumps(data)
        response = self._do_request('post', url, data=payload)
        data = self._get_response_data(response)
        return self._unserialize(data)


class ModelRunCollection(BaseCollection):
    """Access the 'model_run' collection of the REST service."""

    resource = modelstatus.resources.ModelRun
    resource_name = 'model_run'

    def latest(self, data_provider):
        """
        Return the latest model run from the specified data_provider, or None
        if no model run was found.
        """
        params = {
            'data_provider': data_provider,
            'order_by': [
                '-reference_time',
                '-version',
            ],
            'limit': 1,
        }
        results = self.filter(**params)
        return results[0] if len(results) else None


class DataCollection(BaseCollection):
    """Access the 'data' collection of the REST service."""

    resource = modelstatus.resources.Data
    resource_name = 'data'
