import dateutil.parser
import datetime
import time

import modelstatus.utils
import modelstatus.exceptions


class BaseResource(modelstatus.utils.SerializeBase):
    required_parameters = []

    def __init__(self, data):
        """
        Initialize a resource with a Python dictionary.
        The constructor takes a data dictionary instead of a strict parameter
        list because we need to iterate over the parameters anyway and assign
        them to the class. It's simpler and DRY-er just to specify them once,
        in the 'required_parameters' list.
        """
        [setattr(self, key, value) for key, value in data.iteritems()]
        self.validate()
        self.initialize()

    def initialize(self):
        """Do variable initialization, overridden by subclasses"""
        pass

    def validate(self):
        """
        Data validation, run before initialize(). May be overridden by
        subclasses. May throw exceptions.
        """
        try:
            for required_parameter in self.required_parameters:
                getattr(self, required_parameter)
        except:
            raise TypeError("Required parameter %s not specified" % required_parameter)


class ModelRun(BaseResource):
    required_parameters = ['id', 'data_provider', 'reference_time', 'created_date', 'version', 'data']
    __serializable__ = ['id', 'data_provider', 'reference_time', 'created_date', 'version', 'data']

    def initialize(self):
        self.reference_time = dateutil.parser.parse(self.reference_time)
        self.created_date = dateutil.parser.parse(self.created_date)
        self.data = [Data(x) for x in self.data]

    def age(self):
        """
        Return model run age, in seconds
        """
        now = datetime.datetime.now()
        now_ts = time.mktime(now.timetuple())
        then_ts = time.mktime(self.reference_time.timetuple())
        return int(now_ts - then_ts)

    def serialize_reference_time(self, value):
        return self._serialize_datetime(value)

    def serialize_created_date(self, value):
        return self._serialize_datetime(value)

    def serialize_data(self, value):
        return [x.serialize() for x in value]

    def __repr__(self):
        return "ModelRun id=%d data_provider=%s reference_time=%s version=%d" % \
            (self.id, self.data_provider, self.reference_time.isoformat(), self.version)


class Data(BaseResource):
    required_parameters = ['id', 'model_run_id', 'format', 'href']
    __serializable__ = ['id', 'model_run_id', 'format', 'href']

    def __repr__(self):
        return "Data id=%d model_run_id=%d format=%s href=%s" % \
            (self.id, self.model_run_id, self.format, self.href)
