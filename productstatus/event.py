"""
The productstatus.event module is an interface to the ZeroMQ event publisher
daemon running on a Productstatus server.
"""

import zmq


class Message(dict):
    """
    A ZeroMQ event message.
    """

    def __getattr__(self, name):
        return self[name]


class Listener(object):
    """
    ZeroMQ event listener client that provides a simple interface for fetching
    the next event from the queue.
    """

    def __init__(self, connection_string):
        """
        Set up a connection to the Productstatus server, with TCP keepalive enabled.
        """
        self.connection_string = connection_string
        self.context = zmq.Context(1)
        self.socket = self.context.socket(zmq.SUB)
        # enable TCP keepalive
        self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        # keepalive packet sent each N seconds
        self.socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        # keepalive packet sent each N seconds
        self.socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        # number of missed packets to mark connection as dead
        self.socket.setsockopt(zmq.TCP_KEEPALIVE_CNT, 2)
        self.socket.connect(connection_string)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, u'')

    def get_next_event(self):
        """
        Block until a message is received, and return the message object.
        """
        return Message(self.socket.recv_json())