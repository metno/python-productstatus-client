import unittest
import datetime
import dateutil.tz
import copy

import modelstatus


VALID_MODEL_RUN_FIXTURE = {
    'id': 'cbcf639e-48e0-4a91-b909-a58a50cd0326',
    'data_provider': 'arome_metcoop_2500m',
    'reference_time': '2015-01-19T16:04:40Z',
    'created_date': '2015-01-19T16:04:40Z',
    'version': 1337,
    'data': [
        {
            'model_run_id': 'edd509cc-c23e-4a3c-a44c-5d17d0b624dc',
            'id': 1,
            'format': 'netcdf4',
            'href': 'opdata:///arome2_5/arome_metcoop_default2_5km_20150112T06Z.nc',
            'created_time': '2015-01-12T08:36:03Z'
        }
    ]
}


class CollectionTest(unittest.TestCase):
    BASE_URL = 'http://localhost'

    def setUp(self):
        self.store = modelstatus.ModelRunCollection(self.BASE_URL, True)

    def test_get_collection_url(self):
        self.assertEqual(self.store.get_collection_url(), "%s/api/v1/model_run/" % self.BASE_URL)

    def test_get_resource_url(self):
        id = 'cbcf639e-48e0-4a91-b909-a58a50cd0326'
        self.assertEqual(self.store.get_resource_url(id), "%s/api/v1/model_run/%s/" % (self.BASE_URL, id))

    def test_unserialize(self):
        json_string = '{"foo":"bar"}'
        json_data = {"foo": "bar"}
        self.assertEqual(self.store._unserialize(json_string), json_data)


class ModelRunTest(unittest.TestCase):
    """Tests the ModelRun resource"""

    def test_initialize_with_invalid_reference_time(self):
        invalid_fixture = copy.deepcopy(VALID_MODEL_RUN_FIXTURE)
        invalid_fixture['reference_time'] = 'in a galaxy far, far away'
        with self.assertRaises(ValueError):
            modelstatus.ModelRun(invalid_fixture)

    def test_initialize_with_correct_data(self):
        model_run = modelstatus.ModelRun(VALID_MODEL_RUN_FIXTURE)
        self.assertIsInstance(model_run.id, str)
        self.assertIsInstance(model_run.data_provider, str)
        self.assertIsInstance(model_run.reference_time, datetime.datetime)
        self.assertIsInstance(model_run.version, int)

    def test_age(self):
        model_run = modelstatus.ModelRun(VALID_MODEL_RUN_FIXTURE)
        model_run.reference_time = datetime.datetime.now() - dateutil.relativedelta.relativedelta(minutes=7)
        age = model_run.age()
        self.assertEqual(age, 420)
