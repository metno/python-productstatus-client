import datetime
import dateutil.tz


def build_url(*args):
    """
    Join a list of strings into a slash-separated string, stripping any leading
    slashes but including the trailing slash.
    """
    return '/'.join([x.strip('/') for x in args]) + '/'


def get_utc_now():
    """
    Return a time-zone aware DateTime object with the current date and time
    """
    return datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())


class SerializeBase(object):
    __serializable__ = []

    def serialize(self):
        """
        Create JSON encodable representation of internal data structure.
        """
        serialized = {}
        for key in self.__serializable__:
            func_name = 'serialize_' + key
            func = getattr(self, func_name, None)
            serialized[key] = getattr(self, key, None)
            if callable(func):
                serialized[key] = func(serialized[key])
            elif hasattr(serialized[key], 'serialize'):
                serialized[key] = serialized[key].serialize()
        return serialized

    def unserialize(self, data):
        """
        Load internal data structure from JSON decoded dictionary.
        """
        for key in self.__serializable__:
            func_name = 'unserialize_' + key
            func = getattr(self, func_name, None)
            if callable(func):
                value = func(data[key])
            else:
                value = data[key]
            setattr(self, key, value)

    def _serialize_datetime(self, value):
        """
        Return a time zone-aware ISO 8601 string.
        """
        utc_time = value.astimezone(tz=dateutil.tz.tzutc())
        return utc_time.isoformat().replace(' ', 'T').replace('+00:00', 'Z')

    def _unserialize_datetime(self, value):
        """
        Return a DateTime object from a ISO 8601 string.
        """
        return dateutil.parser.parse(value)
