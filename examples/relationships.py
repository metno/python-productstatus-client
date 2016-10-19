import productstatus.api

api = productstatus.api.Api(
    'https://productstatus.met.no'
)

datainstance = api['/api/v1/datainstance/25e12e35-b21e-4ef5-a186-ce8daa43b53f/']

print('Object:', datainstance)
print('URL:', datainstance.url)
print('Reference time:', datainstance.data.productinstance.reference_time)
print('Institution:', datainstance.data.productinstance.product.institution.name)
