import unittest
import httmock
import datetime
import dateutil.tz
import json

import productstatus.api
import productstatus.exceptions


BASE_URL = 'http://192.168.254.254'
BLANK_UUID = '00000000-0000-0000-0000-000000000000'


foo_unserialized = {
    "id": "66340f0b-2c2c-436d-a077-3d939f4f7283",
    "slug": "bar",
    "created": "2015-01-01T00:00:00+0000",
    "resource_uri": "/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/",
    "bar": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
    "number": 1,
    "text": "baz"
}


@httmock.all_requests
def req_404(url, request):
    return {
        'status_code': 404,
        'content': b'Not found'
    }


@httmock.all_requests
def req_500(url, request):
    return {
        'status_code': 500,
        'content': b'Internal server error'
    }


@httmock.urlmatch(path=r'^/api/v1/$')
def req_schema(url, request):
    return b"""
    {
        "foo": {
            "list_endpoint": "/api/v1/foo/",
            "schema": "/api/v1/foo/schema/"
        }
    }
    """


@httmock.urlmatch(method='post', path=r'^/api/v1/foo/$')
def req_post_foo_resource(url, request):
    headers = {'Location': '/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/'}
    return httmock.response(201, {}, headers, None, 5, request)


@httmock.urlmatch(method='put', path=r'^/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/$')
def req_put_foo_resource(url, request):
    return {
        'status_code': 204
    }


@httmock.urlmatch(path=r'^/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/$')
def req_foo_resource(url, request):
    return bytes(json.dumps(foo_unserialized).encode('UTF-8'))


@httmock.urlmatch(path=r'^/api/v1/foo/$', query=r'foo=bar(&offset=0)?$')
def req_filter_foo_resource(url, request):
    return b"""
    {
        "meta": {
            "limit": 1,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 2
        },
        "objects": [
            {
                "id": "66340f0b-2c2c-436d-a077-3d939f4f7283",
                "slug": "bar",
                "created": "2015-01-01T10:00:00Z",
                "resource_uri": "/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/",
                "bar": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
                "number": 1,
                "text": "baz"
            }
        ]
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/$', query=r'slug=bar$')
def req_search_foo_slug_resource(url, request):
    return b"""
    {
        "meta": {
            "limit": 1,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 1
        },
        "objects": [
            {
                "id": "66340f0b-2c2c-436d-a077-3d939f4f7283",
                "slug": "bar",
                "created": "2015-01-01T10:00:00Z",
                "resource_uri": "/api/v1/foo/66340f0b-2c2c-436d-a077-3d939f4f7283/",
                "bar": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
                "number": 1,
                "text": "baz"
            }
        ]
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/$', query=r'slug=notfound$')
def req_search_foo_slug_resource_no_results(url, request):
    return b"""
    {
        "meta": {
            "limit": 1,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 0
        },
        "objects": []
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/$', query=r'foo=bar&offset=1?$')
def req_filter_foo_resource_page2(url, request):
    return b"""
    {
        "meta": {
            "limit": 1,
            "next": null,
            "offset": 1,
            "previous": null,
            "total_count": 2
        },
        "objects": [
            {
                "id": "8a3c4389-8911-452e-b06b-dd7238c787a5",
                "slug": "bar",
                "created": "2015-01-01T10:00:00Z",
                "resource_uri": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
                "bar": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
                "number": 5,
                "text": "foo"
            }
        ]
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/$')
def req_bar_resource(url, request):
    return b"""
    {
        "id": "8a3c4389-8911-452e-b06b-dd7238c787a5",
        "slug": "baz",
        "created": "2015-01-01T10:00:00Z",
        "resource_uri": "/api/v1/foo/8a3c4389-8911-452e-b06b-dd7238c787a5/",
        "bar": null,
        "number": null,
        "text": "baz"
    }
    """


@httmock.urlmatch(path=r'^/api/v1/foo/schema/$')
def req_foo_schema(url, request):
    return b"""
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
                "blank": true,
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
            "slug": {
                "blank": false,
                "default": "slugify",
                "help_text": "Unicode string data. Ex: \\"Hello World\\"",
                "nullable": false,
                "primary_key": false,
                "readonly": false,
                "type": "string",
                "unique": true,
                "verbose_name": "slug"
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
                "blank": true,
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
        self.api = productstatus.api.Api(BASE_URL, verify_ssl=False)
        with httmock.HTTMock(req_schema):
            self.api.foo  # download the schema and cache the 'foo' type

    def test_resource_collection(self):
        """
        Test that a resource collection object is generated when accessing it
        as a member of Api.
        """
        self.assertIsInstance(self.api.foo, productstatus.api.ResourceCollection)
        self.assertEqual(self.api.foo._resource_name, 'foo')
        self.assertEqual(self.api.foo._url, BASE_URL + '/api/v1/foo/')
        self.assertEqual(self.api.foo._schema_url, BASE_URL + '/api/v1/foo/schema/')

    def test_nonexistent_resource_type(self):
        """
        Test that an exception is thrown when accessing a resource type that is
        unsupported on the Productstatus server.
        """
        with self.assertRaises(productstatus.exceptions.ResourceTypeNotFoundException):
            with httmock.HTTMock(req_schema):
                self.api.bar  # try to download the non-existent schema for 'bar'

    def test_resource(self):
        """
        Test that resource members can be accessed, and are converted into
        proper Python types such as DateTime, int, etc.
        """
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        self.assertIsInstance(resource, productstatus.api.Resource)
        with httmock.HTTMock(req_foo_resource, req_foo_schema):
            self.assertIsInstance(resource.created, datetime.datetime)
            self.assertIsInstance(resource.bar, productstatus.api.Resource)
            self.assertEqual(resource.text, "baz")
            self.assertEqual(resource.number, 1)

    def test_resource_slug(self):
        """!
        @brief Test that resources can be accessed using their slug.
        """
        with httmock.HTTMock(req_search_foo_slug_resource, req_foo_schema):
            resource = self.api.foo['bar']
            self.assertIsInstance(resource, productstatus.api.Resource)

    def test_nonexistant_resource_slug(self):
        """!
        @brief Test that non-existant resources accessed using their slug throws a 404 error.
        """
        with httmock.HTTMock(req_search_foo_slug_resource_no_results, req_foo_schema):
            with self.assertRaises(productstatus.exceptions.ResourceNotFoundException):
                resource = self.api.foo['notfound']

    def test_post_resource(self):
        """
        Test that resource members can be created.
        """
        resource = self.api.foo.create()
        with httmock.HTTMock(req_post_foo_resource, req_foo_resource, req_foo_schema):
            self.assertIsNone(resource.id)
            resource.text = 'baz'
            resource.save()
            self.assertEqual(resource.text, 'baz')

    def test_put_resource(self):
        """
        Test that resource members can be updated.
        """
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        with httmock.HTTMock(req_put_foo_resource, req_foo_resource, req_bar_resource, req_foo_schema):
            resource.text = 'baz'
            resource.save()
            self.assertEqual(resource.text, 'baz')

    def test_serialize_resource(self):
        """
        Test that resources are properly serialized.
        """
        global foo_unserialized
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        with httmock.HTTMock(req_put_foo_resource, req_foo_resource, req_bar_resource, req_foo_schema):
            serialized = resource._serialize()
            foo_serialized = json.dumps(foo_unserialized, sort_keys=True)
            self.assertEqual(serialized, foo_serialized)

    def test_nonexistent_resource(self):
        """
        Test that an exception is thrown when accessing an object that does not
        exist on the server.
        """
        resource = self.api.foo[BLANK_UUID]
        with self.assertRaises(productstatus.exceptions.ResourceNotFoundException):
            with httmock.HTTMock(req_foo_schema, req_404):
                resource.id

    def test_server_error(self):
        """
        Test that an exception is thrown when the server is unavailable.
        """
        resource = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
        with self.assertRaises(productstatus.exceptions.ServiceUnavailableException):
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

    def test_queryset(self):
        """
        Test that resource collections return a QuerySet when using objects().
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        self.assertIsInstance(qs, productstatus.api.QuerySet)

    def test_queryset_filter(self):
        """
        Test that resource collections can be filtered.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.filter(foo='bar')
        self.assertEqual(qs._filters['foo'], 'bar')
        with httmock.HTTMock(req_filter_foo_resource, req_foo_schema):
            resource = qs[0]
            self.assertIsInstance(resource.created, datetime.datetime)
            self.assertIsInstance(resource.bar, productstatus.api.Resource)
            self.assertEqual(resource.text, "baz")
            self.assertEqual(resource.number, 1)

    def test_naive_timestamp_filter(self):
        """
        Test that timezone-naive datetime objects cannot be used for filtering.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        dt = datetime.datetime(year=2016,
                               month=1,
                               day=15,
                               hour=12,
                               minute=13,
                               second=37)
        with self.assertRaises(productstatus.exceptions.InvalidFilterDataException):
            qs.filter(created=dt)

    def test_filter_ephemeral_resource(self):
        """!
        @brief Test that ephemeral resources cannot be used to filter queries.
        """
        with httmock.HTTMock(req_schema, req_foo_schema):
            qs = self.api.foo.objects
            ephemeral = self.api.foo.create()
            with self.assertRaises(productstatus.exceptions.InvalidFilterDataException):
                qs.filter(bar=ephemeral)

    def test_query_normalize_utc(self):
        """
        Test that datetime objects used in filtering are sent as UTC.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        dt = datetime.datetime(year=2016,
                               month=1,
                               day=15,
                               hour=12,
                               minute=13,
                               second=37,
                               tzinfo=dateutil.tz.gettz('GMT-05:00'))
        qs.filter(created=dt)
        self.assertEqual(qs._filters['created'], '2016-01-15T17:13:37Z')

    def test_queryset_filter_resource_object(self):
        """
        Test that filtering by resource objects resolves into a correct URL.
        """
        with httmock.HTTMock(req_schema, req_foo_schema, req_foo_resource):
            qs = self.api.foo.objects
            foo = self.api.foo['66340f0b-2c2c-436d-a077-3d939f4f7283']
            qs.filter(foo=foo)
        self.assertEqual(qs._filters['foo'], '66340f0b-2c2c-436d-a077-3d939f4f7283')

    def test_queryset_filter_page2(self):
        """
        Test that resource collections can be filtered.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.filter(foo='bar')
        with httmock.HTTMock(req_filter_foo_resource_page2, req_foo_schema):
            resource = qs[1]
            self.assertIsInstance(resource.created, datetime.datetime)
            self.assertIsInstance(resource.bar, productstatus.api.Resource)
            self.assertEqual(resource.text, "foo")
            self.assertEqual(resource.number, 5)

    def test_queryset_filter_walk(self):
        """
        Test that we can iterate through filter results.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.filter(foo='bar')
        with httmock.HTTMock(req_filter_foo_resource, req_filter_foo_resource_page2, req_foo_schema):
            count = qs.count()
            while count != 0:
                count -= 1
                resource = qs[count]
                self.assertIsInstance(resource.created, datetime.datetime)

    def test_queryset_count(self):
        """
        Test that resource collections are counted.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.filter(foo='bar')
        with httmock.HTTMock(req_filter_foo_resource):
            self.assertEqual(qs.count(), 2)

    def test_queryset_limit(self):
        """
        Test that resource collections can be constrained with a result limit.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.limit(55)
        self.assertEqual(qs._filters['limit'], 55)

    def test_queryset_limit_int(self):
        """
        Test that limit() only accepts integers.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        with self.assertRaises(ValueError):
            qs.limit('foo')

    def test_queryset_order_by(self):
        """
        Test that querysets can be ordered.
        """
        with httmock.HTTMock(req_schema):
            qs = self.api.foo.objects
        qs.order_by('-foo', 'bar')
        self.assertEqual(qs._filters['order_by'], ['-foo', 'bar'])
