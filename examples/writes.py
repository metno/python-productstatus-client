import productstatus.api
import datetime

import requests.packages.urllib3
import requests.packages.urllib3.exceptions

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Writing objects requires a username and API key
api = productstatus.api.Api(
    'https://productstatus-staging.met.no',
    verify_ssl=False,
    username='admin',
    api_key='5bcf851f09bc65043d987910e1448781fcf4ea12',
)

# Creates a Python object which is in-memory until persisted remotely.
productinstance = api.productinstance.create()

# Set some properties.
productinstance.reference_time = productstatus.utils.get_utc_now()
productinstance.product = api.product['ecmwf-atmospheric-model-bc-surface']
productinstance.version = 1

# Persist the object remotely. This will trigger a new Kafka event as well.
productinstance.save()

# The object now has an URI, and we have the latest copy of the remote object.
print(productinstance.resource_uri)
print(productinstance.created)

# With a new ProductInstance object, you can create your time steps:
data = api.data.create()
data.productinstance = productinstance
data.time_period_begin = productstatus.utils.get_utc_now()
data.time_period_end   = productstatus.utils.get_utc_now()
data.save()

# And then connect a physical file to that time step.
datainstance = api.datainstance.create()
datainstance.url = 'file:///lustre/storeA/projects/metproduction/products/foobar/myfile.nc'
datainstance.data = data
datainstance.format = api.dataformat['netcdf']
datainstance.servicebackend = api.servicebackend['lustre-a']
datainstance.expires = productstatus.utils.get_utc_now() + datetime.timedelta(days=1)
datainstance.save()
