import unittest
import httmock
import datetime

import modelstatus.api


BASE_URL = 'http://255.255.255.255'


@httmock.all_requests
def req_404(url, request):
    return {
        'status_code': 404,
        'content': 'Not found'
    }


@httmock.all_requests
def req_500(url, request):
    return {
        'status_code': 500,
        'content': 'Internal server error'
    }


@httmock.urlmatch(path=r'^/api/v1/$')
def req_schema(url, request):
    return """
    {
        "foo": {
            "list_endpoint": "/api/v1/foo/",
            "schema": "/api/v1/foo/schema/"
        }
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/$')
def req_foo_resource(url, request):
    return """
    {
        "id": "66340f0b-2c2c-436d-a077-3d939f4f7283",
        "created": "2015-01-01T00:00:00Z",
        "resource_uri": "/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/",
        "bar": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
        "number": 1,
        "text": "baz"
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/$')
def req_bar_resource(url, request):
    return """
    {
        "id": "8a3c4389-8911-452e-b06b-dd7238c787a5",
        "created": "2015-01-01T10:00:00Z",
        "resource_uri": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
        "bar": null,
        "number": null,
        "text": "baz"
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/schema/$')
def req_foo_schema(url, request):
    return """
    {
        "allowed_detail_http_methods": [
            "get",
            "post",
            "put",
            "delete",
            "patch"
        ],
        "allowed_list_http_methods": [
            "get",
            "post",
            "put",
            "delete",
            "patch"
        ],
        "default_format": "application/json",
        "default_limit": 20,
        "fields": {
            "id": {
                "blank": false,
                "default": "94ffde7d-b167-489e-800b-c51aacf721e1",
                "help_text": "Unicode string data. Ex: \\"Hello World\\"",
                "nullable": false,
                "readonly": false,
                "type": "string",
                "unique": true
            },
            "resource_uri": {
                "blank": false,
                "default": "No default provided.",
                "help_text": "Unicode string data. Ex: \\"Hello World\\"",
                "nullable": false,
                "readonly": true,
                "type": "string",
                "unique": false
            },
            "number": {
                "blank": false,
                "default": "No default provided.",
                "help_text": "Integer data. Ex: 2673",
                "nullable": false,
                "readonly": false,
                "type": "integer",
                "unique": false
            },
            "created": {
                "blank": true,
                "default": true,
                "help_text": "A date & time as a string. Ex: \\"2010-11-10T03:07:43\\"",
                "nullable": false,
                "readonly": false,
                "type": "datetime",
                "unique": false
            },
            "text": {
                "blank": false,
                "default": "No default provided.",
                "help_text": "Unicode string data. Ex: \\"Hello World\\"",
                "nullable": false,
                "readonly": false,
                "type": "string",
                "unique": true
            },
            "bar": {
                "blank": false,
                "default": "No default provided.",
                "help_text": "A single related resource. Can be either a URI or set of nested resource data.",
                "nullable": true,
                "readonly": false,
                "related_type": "to_one",
                "type": "related",
                "unique": false
            }
        },
        "filtering": {
        }
    }
    """


class ExternalTest(unittest.TestCase):
    def setUp(self):
        self.api = modelstatus.api.Api(BASE_URL, verify_ssl=False)
        with httmock.HTTMock(req_schema):
            self.api.foo  # download the schema and cache the 'foo' type

    def test_resource_collection(self):
        """
        Test that a resource collection object is generated when accessing it
        as a member of Api.
        """
        self.assertIsInstance(self.api.foo, modelstatus.api.ResourceCollection)
        self.assertEqual(self.api.foo._resource_name, 'foo')
        self.assertEqual(self.api.foo._url, BASE_URL + '/api/v1/foo/')
        self.assertEqual(self.api.foo._schema_url, BASE_URL + '/api/v1/foo/schema/')

    def test_nonexistent_resource_type(self):
        """
        Test that an exception is thrown when accessing a resource type that is
        unsupported on the Modelstatus server.
        """
        with self.assertRaises(modelstatus.exceptions.ResourceTypeNotFoundException):
            with httmock.HTTMock(req_schema):
                self.api.bar  # try to download the non-existent schema for 'bar'

    def test_resource(self):
        """
        Test that resource members can be accessed, and are converted into
        proper Python types such as DateTime, int, etc.
        """
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        self.assertIsInstance(resource, modelstatus.api.Resource)
        with httmock.HTTMock(req_foo_resource, req_foo_schema):
            self.assertIsInstance(resource.created, datetime.datetime)
            self.assertIsInstance(resource.bar, modelstatus.api.Resource)
            self.assertEqual(resource.text, "baz")
            self.assertEqual(resource.number, 1)

    def test_nonexistent_resource(self):
        """
        Test that an exception is thrown when accessing an object that does not
        exist on the server.
        """
        resource = self.api.foo['bar']
        with self.assertRaises(modelstatus.exceptions.ResourceNotFoundException):
            with httmock.HTTMock(req_foo_schema, req_404):
                resource.id

    def test_server_error(self):
        """
        Test that an exception is thrown when the server is unavailable.
        """
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        with self.assertRaises(modelstatus.exceptions.ServiceUnavailableException):
            with httmock.HTTMock(req_foo_schema, req_500):
                resource.id

    def test_foreign_key_resolution(self):
        """
        Test that foreign keys are resolved and converted into Resource objects.
        """
        with httmock.HTTMock(req_schema):
            resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        with httmock.HTTMock(req_foo_resource, req_bar_resource, req_foo_schema):
            bar = resource.bar
            self.assertEqual(bar.text, "baz")
