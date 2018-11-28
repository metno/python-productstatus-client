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

        try:
            self.json_consumer = kafka.KafkaConsumer(*args, **kwargs)
        except ssl_module.SSLError as e:
            raise productstatus.exceptions.SSLException(e)

    @staticmethod
    def create_security_context(verify_ssl=True):
        ctx = ssl_module.create_default_context()
        ctx.protocol = ssl_module.PROTOCOL_TLSv1_2
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        return ctx

    def close(self):
        """!
        @brief Close the Kafka connection.
        """
        self.json_consumer.close()

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

    def get_position(self):
        """!
        @brief Get the offset of the next record that will be fetched
        @returns int.
        """
        assignment = self.json_consumer.assignment()
        if len(assignment) == 0:
            raise productstatus.exceptions.KafkaPartitionAssignment('No partitions assigned')

        if len(assignment) > 1:
            raise productstatus.exceptions.KafkaPartitionAssignment('More than one partition assigned')

        if len(assignment) == 1:
            partition = next(iter(assignment))
            return self.json_consumer.position(partition)

    def get_last_committed_offset(self):
        """!
        @brief Return the last committed offset
        @returns The last committed offset, or None if there was no prior commit.
        """
        assignment = self.json_consumer.assignment()
        if len(assignment) == 0:
            raise productstatus.exceptions.KafkaPartitionAssignment('No partitions assigned')

        if len(assignment) > 1:
            raise productstatus.exceptions.KafkaPartitionAssignment('More than one partition assigned')

        if len(assignment) == 1:
            partition = next(iter(assignment))
            return self.json_consumer.committed(partition)


    def save_position(self):
        """!
        @brief Store the client's position in the message queue.

        When this function is used, Kafka will store the client's message queue
        position. Thus, next time the client is run, it will resume from the
        next message. To use this function properly, you must set `client_id`
        and `group_id` when instantiating the Listener object.
        """
        self.json_consumer.commit()
