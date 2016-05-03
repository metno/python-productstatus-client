"""!
The productstatus.event module is an interface to the Kafka distributed commit log
where Productstatus server publishes its events
"""

import logging
import ssl
import kafka
import json
import uuid

import productstatus.exceptions


def unserialize(message):
    return json.loads(message.decode('utf-8'))


class Message(dict):
    """!
    @brief A Kafka event message.
    """

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError('Attribute %s does not exist' % name)


class Listener(object):
    """!
    @brief Kafka event listener client that provides a simple interface for
    fetching the next event from the queue.
    """

    def __init__(self, *args, ssl=False, ssl_verify=True, **kwargs):
        """!
        @brief Set up a connection to the Kafka instance on Productstatus server.

        Takes the same parameters as the KafkaConsumer() constructor. Client
        and group UUIDs will be auto-generated if not specified.
        """

        if 'client_id' not in kwargs or not kwargs['client_id']:
            kwargs['client_id'] = str(uuid.uuid4())

        if 'group_id' not in kwargs or not kwargs['group_id']:
            kwargs['group_id'] = str(uuid.uuid4())

        kwargs['enable_auto_commit'] = False
        kwargs['value_deserializer'] = unserialize

        self.client_id = kwargs['client_id']
        self.group_id = kwargs['group_id']

        # Handle SSL parameters
        if ssl:
            kwargs['security_protocol'] = 'SSL'
            kwargs['ssl_context'] = Listener.create_security_context(ssl_verify)

        self.json_consumer = kafka.KafkaConsumer(*args, **kwargs)

    @staticmethod
    def create_security_context(verify_ssl=True):
        ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)
        if not verify_ssl:
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def get_next_event(self):
        """!
        @brief Block until a message is received, or a timeout is reached, and
        return the message object. Raises an exception if a timeout is reached.
        @returns a Message object.
        """
        try:
            for message in self.json_consumer:
                return Message(message.value)
        except StopIteration:
            pass
        raise productstatus.exceptions.EventTimeoutException('Timeout while waiting for next event')

    def save_position(self):
        """!
        @brief Store the client's position in the message queue.

        When this function is used, Kafka will store the client's message queue
        position. Thus, next time the client is run, it will resume from the
        next message. To use this function properly, you must set `client_id`
        and `group_id` when instantiating the Listener object.
        """
        self.json_consumer.commit()
