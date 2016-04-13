"""
The productstatus Python module is an object-based HTTP REST interface to the
Productstatus service. Use the `Api` class in the `productstatus.api` module.
"""

def datainstance_has_complete_file_count(datainstance):
    service_backend_uri = datainstance.servicebackend.resource_uri
    format_uri = datainstance.format.resource_uri
    return datainstance.data.productinstance.complete[service_backend_uri][format_uri]['file_count']
