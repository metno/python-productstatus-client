import unittest
import datetime
import dateutil.tz

import productstatus.utils


class SerializeBaseTest(unittest.TestCase):
    def setUp(self):
        self.class_ = productstatus.utils.SerializeBase()

    def test_serialize_datetime_utc(self):
        dt = datetime.datetime.utcfromtimestamp(3661).replace(tzinfo=dateutil.tz.tzutc())
        dt_string = self.class_._serialize_datetime(dt)
        self.assertEqual(dt_string, '1970-01-01T01:01:01Z')

    def test_serialize_datetime_cet(self):
        dt = datetime.datetime.utcfromtimestamp(3661).replace(tzinfo=dateutil.tz.gettz('Europe/Oslo'))
        dt_string = self.class_._serialize_datetime(dt)
        self.assertEqual(dt_string, '1970-01-01T00:01:01Z')

    def test_serialize_datetime_reject_naive(self):
        dt = datetime.datetime.utcfromtimestamp(3661)
        with self.assertRaises(ValueError):
            self.class_._serialize_datetime(dt)


class TestUtilsTest(unittest.TestCase):
    def test_build_url(self):
        url = productstatus.utils.build_url('a', 'b', 'c')
        self.assertEqual(url, 'a/b/c/')

    def test_build_url_slash(self):
        url = productstatus.utils.build_url('/a', '/b/', 'c/')
        self.assertEqual(url, 'a/b/c/')
