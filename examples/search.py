import productstatus.api

api = productstatus.api.Api(
    'https://productstatus.met.no'
)

datainstances = api.datainstance.objects.filter(
    format=api.dataformat['netcdf'],
    servicebackend=api.servicebackend['lustre-a'],
    # double underscore notation does a SQL JOIN and queries foreign objects
    data__productinstance__product=api.product['ecmwf-atmospheric-model-bc-surface'],
)

for index in range(10):  # detects pagination and minimizes requests
    print(datainstances[index].url)
