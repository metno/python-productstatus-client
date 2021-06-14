"""!
The productstatus.event module is an interface to the Kafka distributed commit log
where Productstatus server publishes its events
"""

import logging
import ssl as ssl_module
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

    Note on commiting messages:
        By default, all messages will be auto_commited. Instead, one can commit
        messages manually. Thus, next time the client is run, it will resume
        from the next message (or ant previous message that is not comitted
        yet). To use this function properly, you must set following values when
        instantiating the Listener object:
        - set `client_id` and `group_id`
        - set `enable_auto_commit` = False
        - set auto_offset_reset = "earliest" Due to `auto_offset_reset =
          "earliest"`, one will receive also messages prior to the first time
          connection. If the message at the current distribution time has the
          offsett 500 (arbirary choice), you may want to commit all messages
          with offsetts 1 to 500 in the initial setup.
    """

    def __init__(self, *args, ssl=False, ssl_verify=True, **kwargs):
        """!
        @brief Set up a connection to the Kafka instance on Productstatus server.

        Takes the same parameters as the KafkaConsumer() constructor. Client
        and group UUIDs will be auto-generated if not specified.
        """

        kwargs.setdefault('client_id', str(uuid.uuid4()))
        kwargs.setdefault('group_id', str(uuid.uuid4()))
        kwargs.setdefault('enable_auto_commit', True)
        kwargs.setdefault('value_deserializer', unserialize)

        self.client_id = kwargs['client_id']
        self.group_id = kwargs['group_id']

        # Handle SSL parameters
        if ssl:
            kwargs['security_protocol'] = 'SSL'
            kwargs['ssl_context'] = Listener.create_security_context(ssl_verify)

        try:
            self.json_consumer = kafka.KafkaConsumer(*args, **kwargs)
        except ssl_module.SSLError as e:
            raise productstatus.exceptions.SSLException(e)

    @staticmethod
    def create_security_context(verify_ssl=True):
        ctx = ssl_module.create_default_context()
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        return ctx

    def close(self):
        """!
        @brief Close the Kafka connection.
        """
        self.json_consumer.close()

    def get_next_event(self, return_kafka_offset=False):
        """!
        @brief Block until a message is received, or a timeout is reached, and
        return the message object. Raises an exception if a timeout is reached.

        @param return_kafka_offsett If true, returns offset value on the
            message in the kafka queue.
        @returns Message object or (Message object, offset) object.
        """
        try:
            for message in self.json_consumer:
                if return_kafka_offset:
                    return Message(message.value), message.offset
                else:
                    return Message(message.value)
        except StopIteration:
            pass
        raise productstatus.exceptions.EventTimeoutException('Timeout while waiting for next event')

    def save_position(self, offsets=None):
        """!
        @brief Store the client's position in the message queue.

        Wrap KafkaConsumer.commit()
        """
        self.json_consumer.commit(offsets)
