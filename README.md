# python-modelstatus-client


## Abstract

This is a Python module used to access a Modelstatus REST API server.

The [Modelstatus code](https://github.com/metno/nir) can be found on Github.


## Setting up a development environment

```
cd python-modelstatus-client
virtualenv deps
source deps/bin/activate
python setup.py develop
```


## Running unit tests

```
source deps/bin/activate
nosetests
```


## Making requests

Import the module `modelstatus.api`, and instantiate an `Api` object. You are now ready to use the Modelstatus server.

```
import modelstatus.api

# username and api key is only needed for write access
api = modelstatus.api.Api('https://modelstatus.fqdn', username='foo', api_key='bar')
```

REST API resource collections (e.g. `/api/v1/model/`) can be accessed as objects directly underneath the `Api` object. REST API resources (e.g. `/api/v1/model/f314a536-bb96-4d2a-83cd-9764e2e3e16a/`) can be accessed using indexing:

```
model = api.model['f314a536-bb96-4d2a-83cd-9764e2e3e16a']
print model.name  # 'AROME MetCoOp 2500m'
```

Foreign keys on resources are automatically resolved into objects:

```
print model.institution.name  # 'MET Norway'
```

You can run filtering queries to find the object you are looking for:

```
model_runs = api.model_run.objects
model_runs.filter(model=model, reference_time=datetime.datetime(2015, 1, 1))
model_runs.order_by('-version')
model_runs.limit(2)
print model_runs.count()  # 2
model_run = model_runs[0]
print model_run.model.resource_uri == model.resource_uri  # True
```

Creating new objects are done using the resource collection:

```
new_model_run = api.model_run.create()
new_model_run.reference_time = datetime.datetime.now()
new_model_run.model = model
new_model_run.save()
print new_model_run.id  # '4560279d-ef3e-49ae-bf2e-0dabac1b9e74'
```

You can also edit an existing object:

```
model_run.reference_time += datetime.timedelta(seconds=1)
model_run.save()
```

Lastly, you can access the schema to get an idea of how the data model looks like:

```
print api.model_run.schema  # { 'huge': 'dictionary' }
```


## Command-line utility

The Modelstatus client ships with a handy "swiss army knife" that enables you to read and write remote objects from the command line.

Some examples of usage follow. Below, we create a new service backend object:

```
$ python modelstatus/cli.py \
    --username X \
    --api_key Y \
    http://localhost:8000 \
    service_backend create \
    --name /dev/null \
    --documentation_url 'https://example.com'
{
    "created": "2015-11-10T17:35:17+0000",
    "documentation_url": "https://example.com",
    "id": "013f06f9-8cf3-4123-94b1-4206b2807cbd",
    "modified": "2015-11-10T17:35:17+0000",
    "name": "/dev/null",
    "resource_uri": "/api/v1/service_backend/013f06f9-8cf3-4123-94b1-4206b2807cbd/"
}
```

Searching by specific parameters. If you omit the parameters, all results will be returned.

```
$ python modelstatus/cli.py http://localhost:8000 model_run search --reference_time 2015-01-01T12:00:00Z --model 8efab026-434e-4baf-b8ed-d921a1b0b427
[
    {
        "created": "2015-11-10T17:27:13+0000",
        "id": "1ddb75c9-d5b4-49a8-9c27-79a47dd396b5",
        "model": "/api/v1/model/8efab026-434e-4baf-b8ed-d921a1b0b427/",
        "modified": "2015-11-10T17:27:13+0000",
        "reference_time": "2015-01-01T12:00:00+0000",
        "resource_uri": "/api/v1/model_run/1ddb75c9-d5b4-49a8-9c27-79a47dd396b5/",
        "version": 1
    },
    {
        "created": "2015-11-10T17:27:20+0000",
        "id": "3789bc4b-eeb1-488b-96df-a1b2e680bf27",
        "model": "/api/v1/model/8efab026-434e-4baf-b8ed-d921a1b0b427/",
        "modified": "2015-11-10T17:27:20+0000",
        "reference_time": "2015-01-01T12:00:00+0000",
        "resource_uri": "/api/v1/model_run/3789bc4b-eeb1-488b-96df-a1b2e680bf27/",
        "version": 2
    }
]
```

Requesting a specific resource item:

```
$ python modelstatus/cli.py http://localhost:8000 model get 8efab026-434e-4baf-b8ed-d921a1b0b427
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
    "level": 0,
    "lft": 1,
    "modified": "2015-11-10T11:37:58+0000",
    "name": "Nordic",
    "parent": null,
    "prognosis_length": 60,
    "projection": "/api/v1/projection/c2b3d081-bb4d-4dea-975b-0126bdab6691/",
    "resource_uri": "/api/v1/model/8efab026-434e-4baf-b8ed-d921a1b0b427/",
    "rght": 2,
    "time_steps": 60,
    "tree_id": 1,
    "wdb_data_provider": "nordic_roms"
}
```
