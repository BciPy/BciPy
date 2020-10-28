import unittest

from collections import abc
import tempfile
import shutil
import pickle

from bcipy.helpers.load import (load_json_parameters, load_signal_model,
                                copy_parameters)
from bcipy.helpers.parameters import Parameters

class TestLoad(unittest.TestCase):
    """This is Test Case for Loading BCI data."""

    def setUp(self):
        """set up the needed path for load functions."""

        self.parameters = 'bcipy/parameters/parameters.json'
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_json_parameters_returns_dict(self):
        """Test load parameters returns a Python dict."""

        # call the load parameters function
        parameters = load_json_parameters(self.parameters)

        # assert that load function turned json parameters into a dict-like obj
        self.assertEqual(type(parameters), Parameters)
        self.assertTrue(isinstance(parameters, abc.MutableMapping))

    def test_load_json_parameters_throws_error_on_wrong_path(self):
        """Test load parameters returns error on entering wrong path."""

        # call the load parameters function with incorrect path
        with self.assertRaises(Exception):
            load_json_parameters('/garbage/dir/wont/work')

    def test_load_classifier(self):
        """Test load classifier can load pickled file when given path."""

        # create a pickle file to save a pickled json
        pickle_file = self.temp_dir + "save.p"
        pickle.dump(self.parameters, open(pickle_file, "wb"))

        # Load classifier
        unpickled_parameters = load_signal_model(pickle_file)

        # assert the same data was returned
        self.assertEqual(unpickled_parameters, (self.parameters, pickle_file))

    def test_copy_default_parameters(self):
        """Test that default parameters can be copied."""
        path = copy_parameters(destination=self.temp_dir)

        self.assertTrue(path != self.parameters)

        copy = load_json_parameters(path)
        self.assertTrue(type(copy), 'dict')

        parameters = load_json_parameters(self.parameters)
        self.assertEqual(copy, parameters)


if __name__ == '__main__':
    unittest.main()
