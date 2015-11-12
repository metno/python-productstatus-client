import copy
import requests
import requests.auth
import json
import dateutil.parser

import modelstatus.utils
import modelstatus.exceptions


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

    def __init__(self, base_url, verify_ssl=True, username=None, api_key=None, timeout=3):
        """
        Initialize the Api class.

        @param base_url The root URL where the Modelstatus server serves data.
        @param verify_ssl Whether or not to verify SSL certificates.
        @param username Client API username.
        @param api_key Client API key.
        @param timeout Request timeout in seconds.
        """
        self._base_url = base_url
        self._url_prefix = '/api/v1/'
        self._url = modelstatus.utils.build_url(self._base_url, self._url_prefix)
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._session = requests.Session()
        self._session.verify = self._verify_ssl
        self._session.headers.update({'content-type': 'application/json'})
        if username and api_key:
            self._session.auth = TastypieApiKeyAuth(username, api_key)
        self._resource_collection = {}
        self._schema = {}

    def _do_request(self, method, *args, **kwargs):
        """
        Run a request through the requests API. This function wraps
        self.session.{get,post,patch,put,delete} and adds exception handling.

        Returns a response object.
        """
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self._timeout
        try:
            response = self._session.request(method, *args, **kwargs)
        except requests.exceptions.ConnectionError, e:
            raise modelstatus.exceptions.ServiceUnavailableException("Could not connect: %s" % unicode(e))

        self._raise_response_exceptions(response)
        return response

    def _get_response_data(self, response):
        """
        Get unserialized contents from a response object.
        """
        if response.content:
            return self._unserialize(response.content)
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
        response = self._do_request('get', self._url)
        self._schema = self._get_response_data(response)

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

    def __repr__(self):
        """
        Return a human-readable string representing this Api object.
        """
        return '<Modelstatus API at %s>' % self._url


class QuerySet(object):
    """
    The QuerySet class facilitates listing and filtering a resource collection.

    Example usage:
    --------------
    qs = api.model_run.objects  # instantiates a QuerySet
    qs.filter(model=api.model['66340f0b-2c2c-436d-a077-3d939f4f7283'], reference_time=datetime.datetime.now())
    qs.order_by('-version')  # order by version field, descending
    qs.limit(5)  # limit query to 5 results
    qs.count()  # returns total matches, regardless of limit
    qs[2]  # returns the 3rd element matching the criteria
    """

    def __init__(self, api, collection):
        self._api = api
        self._collection = collection
        self._filters = {}
        self._results = {}

    def _relative_item_index(self, index):
        """
        Convert an item's absolute list position to the relative list position
        in self._results['objects']. Returns None if the object is not locally cached.
        """
        if not self._results:
            return None
        offset = self._results['meta']['offset']
        limit = self._results['meta']['limit']
        if index < offset or index >= limit + offset:
            return None
        return index - offset

    def filter(self, **kwargs):
        """
        Add a search constraint and return a reference to self.
        """
        self._results = {}
        [self._add_filter(key, value) for key, value in kwargs.iteritems()]
        return self

    def all(self):
        """
        Deletes all search constraints and return a reference to self.
        """
        self._filters = {}
        return self.filter()

    def order_by(self, *args):
        """
        Apply list ordering. Sorted ascending by default. Prefix member names
        with a minus sign to have descending order.
        """
        return self.filter(order_by=list(args))

    def limit(self, limit):
        """
        Limit the number of results returned from the server.
        """
        return self.filter(limit=int(limit))

    def execute(self):
        """
        Fetch results from the server.
        """
        response = self._api._do_request('get', self._collection._url, params=self._filters)
        self._results = self._api._get_response_data(response)

    def execute_if_empty(self):
        """
        Ensure there exists some search results.
        """
        if not self._results:
            self.execute()

    def count(self):
        """
        Return the number of results in the search query.
        """
        self.execute_if_empty()
        return self._results['meta']['total_count']

    def _add_filter(self, key, value):
        """
        Add a filter to the search query, serializing if neccessary.
        """
        if isinstance(value, modelstatus.api.Resource):
            self._filters[key] = value.id
        else:
            self._filters[key] = value

    def __getitem__(self, index):
        """
        Return the Resource of Nth index in the search results, running a
        remote request if needs be.
        """
        relative_index = self._relative_item_index(index)
        if relative_index is None or not self._results:
            self.filter(offset=index)
            self.execute()
            relative_index = self._relative_item_index(index)
        if relative_index is None:
            raise IndexError('Out of range: %d' % index)
        item = self._results['objects'][relative_index]
        return Resource(self._api, self._collection, item['id'], item)

    def __repr__(self):
        """
        Return a human-readable string representing this query set.
        """
        return '<QuerySet on %s>' % self._collection._url


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

    def create(self):
        """
        Create a new, temporary Resource object that might be saved, and thus
        stored on the server.
        """
        return Resource(self._api, self, None)

    def _get_schema_from_server(self):
        """
        Retrieve from the server the data model schema for this resource type.
        """
        response = self._api._do_request('get', self._schema_url)
        self._schema = self._api._get_response_data(response)

    def __getitem__(self, id):
        """
        Resource accessor. Will create and return a Resource instance pointing
        to a specific resource.
        """
        return Resource(self._api, self, id)

    def __getattr__(self, name):
        """
        Schema or query set accessor.

        Schema accessor returns a dictionary with the schema for this
        particular resource type. It is retrieved from the server unless it is
        locally cached.

        The query set accessor returns an object which is used to return a list
        of objects.
        """
        if name == 'schema':
            if not self._schema:
                self._get_schema_from_server()
            return self._schema
        elif name == 'objects':
            return QuerySet(self._api, self)

        raise KeyError('Attribute does not exist: %s' % name)

    def __repr__(self):
        """
        Return a human-readable string representing this resource collection object.
        """
        return '<%s ResourceCollection at %s>' % (self._resource_name, self._url)


class Resource(object):
    """
    The Resource class represents a single REST API resource. All data is
    available as class members. The class members are automatically converted
    to their respective types using the resource schema. For instance,
    timestamps are converted into DateTime objects, integers are proper ints,
    and foreign keys point to other Resource objects.
    """

    def __init__(self, api, collection, id, data={}):
        self._api = api
        self._collection = collection
        self._id = id
        if self._id:
            self._url = modelstatus.utils.build_url(self._collection._url, self._id)
        else:
            self._url = None
        self._data = copy.copy(data)
        self._unserialize()

    def save(self):
        """
        Store the locally cached values on the server.
        """
        if self._has_url():
            response = self._api._do_request('put', self._url, data=self._serialize())
        else:
            response = self._api._do_request('post', self._collection._url, data=self._serialize())
            self._url = response.headers['Location']
        self._data = {}  # invalidate local cache

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
            response = self._api._do_request('get', self._url)
            self._data = self._api._get_response_data(response)
        except modelstatus.exceptions.NotFoundException, e:
            raise modelstatus.exceptions.ResourceNotFoundException(e)
        self._unserialize()

    def _ensure_complete_object(self):
        """
        Fetch the resource from the API server if we have an URL and it is not
        already cached.
        """
        if self._has_url() and not self._data:
            self._get_resource_from_server()

    def _serialize(self):
        """
        Return a JSON serialized representation of this resource.
        """
        self._ensure_complete_object()
        data = {}
        for key in self._data.keys():
            data[key] = self._serialize_member(key)
        return json.dumps(data)

    def _serialize_member(self, name):
        """
        Serialize a resource variable into a string, integer, boolean, or null.
        """
        if self._data[name] is None:
            return None

        description = self._collection.schema['fields'][name]
        type_ = description['type']
        if type_ == 'datetime':
            return self._data[name].strftime('%Y-%m-%dT%H:%M:%S%z')
        elif type_ == 'related' and description['related_type'] == 'to_one':
            return self._data[name].resource_uri
        return self._data[name]

    def _unserialize(self):
        """
        Replace all string members with their proper types.
        """
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
        fields = self._collection.schema['fields']
        if name not in fields:
            raise KeyError('Attribute does not exist: %s' % name)
        self._ensure_complete_object()
        if name not in self._data:
            return None
        return self._data[name]

    def __setattr__(self, name, value):
        """
        Attribute setter. Will store data cached locally until saved using save().
        Will only allow setting variables that can be stored on the server, and
        disallow changing read-only attributes.
        """
        if name[0] == '_':
            return object.__setattr__(self, name, value)
        fields = self._collection.schema['fields']
        if name not in fields:
            raise KeyError('Attribute does not exist: %s' % name)
        if fields[name]['readonly']:
            raise AttributeError('Attribute is read only: %s' % name)
        # FIXME: more tests?
        self._ensure_complete_object()
        self._data[name] = value

    def __repr__(self):
        """
        Return a human-readable string representing this resource object.
        """
        if self._has_url():
            return '<Resource at %s>' % self.resource_uri
        return '<non-persistent %s Resource>' % self._collection._resource_name


class TastypieApiKeyAuth(requests.auth.AuthBase):
    """
    Django Tastypie requires a special Authorization header format, which is
    implemented by this class.
    """

    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key

    def __call__(self, request):
        request.headers.update({'Authorization': 'ApiKey %s:%s' % (self.username, self.api_key)})
        return request
