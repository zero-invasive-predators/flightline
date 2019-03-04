import unittest
import filecmp
import os
import uuid
import tempfile


from flightline import config_handler

class Resources(object):
    
    @staticmethod
    def generate_temp_space():
        """
        Provides a temp name, temp directory name and uniqueid

        Returns
        -------
        [temp_name, temp_directory_name, unique_id]
        """
        temp_name = tempfile.mkdtemp()
        temp_directory_name = os.path.dirname(temp_name)
        unique_id = uuid.uuid1().clock_seq
        return [temp_name, temp_directory_name, unique_id]

class TestClass(object):
    def __init__(self):
        self.key1 = None
        self.key2 = None
        self.key3 = None


class TestConfigHandler(unittest.TestCase):

    def setUp(self):
        self.temp_name, self.temp_directory_name, self.unique_id = Resources.generate_temp_space()
        self.temp_file = os.path.join(self.temp_directory_name, "projectconfig{0}.json".format(self.unique_id))
        self.test_object = TestClass()
        self.test_object.key1 = 'value1'
        self.key2 = ['listvalue1','listvalue2']
        self.key3 = {'subkey1':'subvalue1','subkey2':2}

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
            os.rmdir(self.temp_name)

    def test_dump_to_projectconfig(self):
        config_handler.dump_to_projectconfig(self.test_object, self.temp_file)
        self.assertTrue(os.path.exists(self.temp_file), msg="JSON file was not created")

    def test_load_from_projectconfig(self):
        config_handler.dump_to_projectconfig(self.test_object, self.temp_file)
        loaded_object = TestClass()
        config_handler.load_from_projectconfig(loaded_object, self.temp_file)
        self.assertEqual(self.test_object.__dict__, loaded_object.__dict__, msg="Dump and load changed the dictionary object. Dict: {0} is not equal to Dict: {1}")


if __name__ == '__main__':
    unittest.main()