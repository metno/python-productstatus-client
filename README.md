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
