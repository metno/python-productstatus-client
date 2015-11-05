import requests
import json
import dateutil.parser

import modelstatus.utils


class Api(object):
    """
    This class provides fluent access to the Modelstatus REST API. Resource
    collections are exposed as members of the Api class, and specific resources
    can be retrieved by indexes.

    The API client tries to be as lazy as possible, and does not make any
    unneccessary requests to the server.

    Examples of use:

    api = Api('http://localhost:8000')
    models = api.model
    arome = models['66340f0b-2c2c-436d-a077-3d939f4f7283']
    print arome.grid_resolution
    """

    def __init__(self, base_url, verify_ssl=True, username=None, password=None):
        """
        Initialize the Api class.

        @param base_url The root URL where the Modelstatus server serves data.
        @param verify_ssl Whether or not to verify SSL certificates.
        @param username Client API username.
        @param password Client API key.
        """
        self._auth = (username, password)
        self._base_url = base_url
        self._url_prefix = '/api/v1/'
        self._url = modelstatus.utils.build_url(self._base_url, self._url_prefix)
        self._verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.auth = self._auth
        self._session.verify = self._verify_ssl
        self._session.headers.update({'content-type': 'application/json'})
        self._resource_collection = {}
        self._schema = {}

    def _get(self, url):
        """
        Run a remote GET request on the server, and return JSON data converted
        to a dictionary.
        """
        response = self._do_request('get', url)
        data = self._get_response_data(response)
        return self._unserialize(data)

    def _do_request(self, method, *args, **kwargs):
        """
        Run a request through the requests API. This function wraps
        self.session.{get,post,patch,put,delete} and adds exception handling.

        Returns a response object.
        """
        try:
            func = getattr(self._session, method)
            response = func(*args, **kwargs)
        except requests.exceptions.ConnectionError, e:
            raise modelstatus.exceptions.ServiceUnavailableException("Could not connect: %s" % unicode(e))

        self._raise_response_exceptions(response)
        return response

    def _get_response_data(self, response):
        """
        Get contents from a response object.
        """
        return response.content

    def _raise_response_exceptions(self, response):
        """
        Conditionally raise exceptions if a response object has errors.
        """
        if response.status_code < 400:
            return
        if response.status_code >= 500:
            exception = modelstatus.exceptions.ServiceUnavailableException
        elif response.status_code == 404:
            exception = modelstatus.exceptions.NotFoundException
        else:
            exception = modelstatus.exceptions.ClientErrorException
        raise exception(response.text)

    def _unserialize(self, data):
        """
        Convert JSON encoded data into a dictionary.
        """
        try:
            return json.loads(data)
        except ValueError, e:
            raise modelstatus.exceptions.UnserializeException(e)

    def _get_schema_from_server(self):
        """
        Retrieve a list of possible resource types from the server.
        """
        self._schema = self._get(self._url)

    def _validate_url_component(self, name):
        """
        Raise an exception if an URL slug cannot be used to determine the
        location of a resource or collection.
        """
        if len(name) == 0:
            raise NameError('URL components cannot be empty')
        if name[0] == '_':
            raise NameError('URL components cannot begin with an underscore')

    def __getattr__(self, name):
        """
        Return a ResourceCollection object which can be used to retrieve
        resources. E.g. api.model_run will point to /api/v1/model_run/.
        """
        if name not in self._resource_collection.keys():
            if not self._schema:
                self._get_schema_from_server()
            if name not in self._schema.keys():
                raise modelstatus.exceptions.ResourceTypeNotFoundException(
                    "The resource '%s' is not supported by the Modelstatus server" % name)
            self._resource_collection[name] = ResourceCollection(self, name)
        return self._resource_collection[name]

    def __getitem__(self, index):
        """
        Provide direct access to an API object. For instance, accessing
        api['/api/v1/model/66340f0b-2c2c-436d-a077-3d939f4f7283/'] will return a
        Resource object.
        """
        prefix_length = len(self._url_prefix)
        if self._url_prefix != index[:prefix_length]:
            raise KeyError('The URL %s is unsupported by this API instance; the URL must begin with %s' %
                           (index, self._url_prefix))
        components = index[prefix_length:].strip('/').split('/')

        # Sanity checks
        if len(components) == 0:
            return self
        for slug in components:
            self._validate_url_component(slug)

        # Load collection
        collection = getattr(self, components[0])
        if len(components) == 1:
            return collection

        # Load resource
        resource = collection[components[1]]
        if len(components) == 2:
            return resource

        raise NameError('The URL %s in unsupported by this API instance; the URL contains too many components' %
                        index)


class ResourceCollection(object):
    """
    The ResourceCollection class is used to retrieve resources from the REST
    API. Resources are accessed using indexes.
    For instance, resource['66340f0b-2c2c-436d-a077-3d939f4f7283'] will return
    a Resource object.
    """

    def __init__(self, api, resource_name):
        self._api = api
        self._resource_name = resource_name
        self._url = modelstatus.utils.build_url(self._api._url, self._resource_name)
        self._schema_url = modelstatus.utils.build_url(self._url, 'schema')
        self._schema = {}

    def _get_schema_from_server(self):
        """
        Retrieve from the server the data model schema for this resource type.
        """
        self._schema = self._api._get(self._schema_url)

    def __getitem__(self, id):
        """
        Resource accessor. Will create and return a Resource instance pointing
        to a specific resource.
        """
        return Resource(self._api, self, id)

    def __getattr__(self, name):
        """
        Schema accessor. Returns a dictionary with the schema for this
        particular resource type. It is retrieved from the server unless it is
        locally cached.
        """
        if name == 'schema':
            if not self._schema:
                self._get_schema_from_server()
            return self._schema
        raise KeyError('Attribute does not exist: %s' % name)


class Resource(object):
    """
    The Resource class represents a single REST API resource. All data is
    available as class members. The class members are automatically converted
    to their respective types using the resource schema. For instance,
    timestamps are converted into DateTime objects, integers are proper ints,
    and foreign keys point to other Resource objects.
    """

    def __init__(self, api, collection, id):
        self._api = api
        self._collection = collection
        self._id = id
        if self._id:
            self._url = modelstatus.utils.build_url(self._collection._url, self._id)
        else:
            self._url = None
        self._data = {}

    def _has_url(self):
        """
        Returns True if this Resource has an URL which can be accessed at the
        server, False otherwise.
        """
        return self._url is not None

    def _get_resource_from_server(self):
        """
        Fetch the resource from the API server.
        """
        if not self._has_url():
            raise modelstatus.exceptions.ModelstatusException('Trying to get an object without a primary key')
        try:
            self._data = self._api._get(self._url)
        except modelstatus.exceptions.NotFoundException, e:
            raise modelstatus.exceptions.ResourceNotFoundException(e)
        for member in self._data.keys():
            self._unserialize_member(member)

    def _unserialize_member(self, name):
        """
        Convert string data into their proper types, according to the resource schema.
        """
        if self._data[name] is None:
            return

        description = self._collection.schema['fields'][name]
        type_ = description['type']
        if type_ == 'integer':
            self._data[name] = int(self._data[name])
        elif type_ == 'datetime':
            self._data[name] = dateutil.parser.parse(self._data[name])
        elif type_ == 'related' and description['related_type'] == 'to_one':
            self._data[name] = self._api[self._data[name]]

    def __getattr__(self, name):
        """
        Attribute accessor. Will load data from the server unless it is cached.
        Enables lazy loading of the resource.
        """
        if not self._data:
            self._get_resource_from_server()
        if name not in self._data:
            raise KeyError('Attribute does not exist: %s' % name)
        return self._data[name]
