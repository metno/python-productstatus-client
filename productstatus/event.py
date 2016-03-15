"""!
The productstatus.event module is an interface to the Kafka distributed commit log
where Productstatus server publishes its events
"""

import kafka
import json
import uuid


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

    def __init__(self, bootstrap_servers, topic='productstatus', timeout=5000, client_id=None, group_id=None):
        """!
        @brief Set up a connection to the Kafka instance on Productstatus server
        """

        if not client_id:
            client_id = unicode(uuid.uuid4())

        if not group_id:
            group_id = unicode(uuid.uuid4())

        self.json_consumer = kafka.KafkaConsumer(topic,
                                                 client_id=client_id,
                                                 group_id=group_id,
                                                 bootstrap_servers=bootstrap_servers,
                                                 enable_auto_commit=False,
                                                 request_timeout_ms=timeout,
                                                 value_deserializer=lambda m: json.loads(m.decode('utf-8')))

    def get_next_event(self):
        """!
        @brief Block until a message is received, and return the message object.
        @returns a Message object.
        """
        return Message(self.json_consumer.next().value)

    def save_position(self):
        """!
        @brief Store the client's position in the message queue.

        When this function is used, Kafka will store the client's message queue
        position. Thus, next time the client is run, it will resume from the
        next message. To use this function properly, you must set `client_id`
        and `group_id` when instantiating the Listener object.
        """
        self.json_consumer.commit()
