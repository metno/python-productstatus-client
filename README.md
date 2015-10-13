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

```
import modelstatus

collection = modelstatus.ModelRunCollection('https://modelstatus.fqdn/modelstatus/v0')
model_run_resource = collection.latest('my_data_provider')
search_results = collection.filter(data_provider='my_data_provider')
model_run_9000 = collection.get(9000)

print model_run_resource
# output: ModelRun id=1 data_provider=my_data_provider reference_time=2015-10-13T00:00:00+00:00 version=1

print [x.href for x in model_run_resource.data]
# output: [u'file:///path/to/my/dataset.nc']
```
