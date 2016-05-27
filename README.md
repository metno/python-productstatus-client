# python-productstatus-client


## Abstract

This is a Python module used to access a Productstatus REST API server.

The [Productstatus code](https://github.com/metno/nir) can be found on Github.


## Setting up a development environment

```
cd python-productstatus-client
virtualenv --python python3 deps
source deps/bin/activate
python setup.py develop
```


## Running unit tests

```
source deps/bin/activate
nosetests
```


## Making requests

Import the module `productstatus.api`, and instantiate an `Api` object. You are now ready to use the Productstatus server.

```
import productstatus.api

# username and api key is only needed for write access
api = productstatus.api.Api('https://productstatus.fqdn', username='foo', api_key='bar')
```

REST API resource collections (e.g. `/api/v1/product/`) can be accessed as objects directly underneath the `Api` object. REST API resources (e.g. `/api/v1/product/f314a536-bb96-4d2a-83cd-9764e2e3e16a/`) can be accessed using indexing:

```
product = api.product['f314a536-bb96-4d2a-83cd-9764e2e3e16a']
print product.name  # 'AROME MetCoOp 2500m'
```

Foreign keys on resources are automatically resolved into objects:

```
print product.institution.name  # 'MET Norway'
```

You can run filtering queries to find the object you are looking for:

```
productinstances = api.productinstance.objects
productinstances.filter(product=product, reference_time=datetime.datetime(2015, 1, 1))
productinstances.order_by('-version')
productinstances.limit(2)
print productinstances.count()  # 2
productinstance = productinstances[0]
print productinstance.product.resource_uri == product.resource_uri  # True
```

Creating new objects are done using the resource collection:

```
new_productinstance = api.productinstance.create()
new_productinstance.reference_time = datetime.datetime.now()
new_productinstance.product = product
new_productinstance.save()
print new_productinstance.id  # '4560279d-ef3e-49ae-bf2e-0dabac1b9e74'
```

You can also edit an existing object:

```
productinstance.reference_time += datetime.timedelta(seconds=1)
productinstance.save()
```

Lastly, you can access the schema to get an idea of how the data model looks like:

```
print api.productinstance.schema  # { 'huge': 'dictionary' }
```


## Command-line utility

The Productstatus client ships with a handy "swiss army knife" that enables you to read and write remote objects from the command line.

Some examples of usage follow. Below, we create a new service backend object:

```
$ python productstatus/cli.py \
    --username X \
    --api_key Y \
    http://localhost:8000 \
    servicebackend create \
    --name /dev/null \
    --documentation_url 'https://example.com'
{
    "created": "2015-11-10T17:35:17+0000",
    "documentation_url": "https://example.com",
    "id": "013f06f9-8cf3-4123-94b1-4206b2807cbd",
    "modified": "2015-11-10T17:35:17+0000",
    "name": "/dev/null",
    "resource_uri": "/api/v1/servicebackend/013f06f9-8cf3-4123-94b1-4206b2807cbd/"
}
```

Searching by specific parameters. If you omit the parameters, all results will be returned.

```
$ python productstatus/cli.py http://localhost:8000 productinstance search --reference_time 2015-01-01T12:00:00Z --product 8efab026-434e-4baf-b8ed-d921a1b0b427
[
    {
        "created": "2015-11-10T17:27:13+0000",
        "id": "1ddb75c9-d5b4-49a8-9c27-79a47dd396b5",
        "product": "/api/v1/product/8efab026-434e-4baf-b8ed-d921a1b0b427/",
        "modified": "2015-11-10T17:27:13+0000",
        "reference_time": "2015-01-01T12:00:00+0000",
        "resource_uri": "/api/v1/productinstance/1ddb75c9-d5b4-49a8-9c27-79a47dd396b5/",
        "version": 1
    },
    {
        "created": "2015-11-10T17:27:20+0000",
        "id": "3789bc4b-eeb1-488b-96df-a1b2e680bf27",
        "product": "/api/v1/product/8efab026-434e-4baf-b8ed-d921a1b0b427/",
        "modified": "2015-11-10T17:27:20+0000",
        "reference_time": "2015-01-01T12:00:00+0000",
        "resource_uri": "/api/v1/productinstance/3789bc4b-eeb1-488b-96df-a1b2e680bf27/",
        "version": 2
    }
]
```

Requesting a specific resource item:

```
$ python productstatus/cli.py http://localhost:8000 product get 8efab026-434e-4baf-b8ed-d921a1b0b427
{
    "bounding_box": "0,0,0,0",
    "contact": "/api/v1/person/8e547c76-6639-450d-a077-5dbcabeb3581/",
    "created": "2015-11-05T11:32:59+0000",
    "grib_center": "ecmf",
    "grib_generating_process_id": "145",
    "grid_resolution": "4000.00000",
    "grid_resolution_unit": "m",
    "id": "8efab026-434e-4baf-b8ed-d921a1b0b427",
    "institution": "/api/v1/institution/a5eb5df1-704c-4450-a7a4-388f7e54c496/",
    "modified": "2015-11-10T11:37:58+0000",
    "name": "Nordic",
    "parent": null,
    "prognosis_length": 60,
    "projection": "/api/v1/projection/c2b3d081-bb4d-4dea-975b-0126bdab6691/",
    "resource_uri": "/api/v1/product/8efab026-434e-4baf-b8ed-d921a1b0b427/",
    "time_steps": 60,
    "wdb_data_provider": "nordic_roms"
}
```

### Exit codes
See cli.py code for the mapping between exceptions and various exit codes.

## Listening for Productstatus message queue events

The event listener is asynchronous, and will queue incoming messages until you fetch them with `get_next_event()`. TCP keepalive is enabled.

```
import productstatus.event
listener = productstatus.event.Listener('tcp://hostname:port')
while True:
    message = listener.get_next_event()  # blocks until the next message is received
    print message.resource     # it behaves as an object...
    print message['resource']  # or a dictionary
```
