import productstatus.api
import productstatus.exceptions

import json

api = productstatus.api.Api(
    'https://productstatus.met.no'
)

# You can easily set up an event listener using the API client. The default operation is to block
# until an event is received, or you can specify a timeout in the constructor.
event_listener = api.get_event_listener()

print('Listening for events...')
print()

# Loop through received events.
while True:
    try:
        event = event_listener.get_next_event()
    except productstatus.exceptions.EventTimeoutException:
        pass
    print(json.dumps(event, indent=4))
    print()

    if event.type == 'heartbeat':
        print('Received heartbeat with timestamp', event.message_timestamp)
    elif event.type == 'resource':
        print('Received resource of type', event.resource)
        if event.resource == 'datainstance':
            datainstance = api[event.uri]
            print('DataInstance URL:', datainstance.url)
            print('DataInstance product name:', datainstance.data.productinstance.product.name)
            print('DataInstance product slug:', datainstance.data.productinstance.product.slug)

    print()
