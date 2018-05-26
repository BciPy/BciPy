import unittest
import numpy as np

from mockito import any, mock, when, unstub

from bcipy.helpers.bci_task_related import alphabet, trial_reshaper
from bcipy.helpers.load import load_json_parameters


class TestAlphabet(unittest.TestCase):

    def test_alphabet_text(self):
        parameters_used = 'bcipy/parameters/parameters.json'
        parameters = load_json_parameters(parameters_used, value_cast=True)

        parameters['is_txt_sti'] = True

        alp = alphabet(parameters)

        self.assertEqual(
            alp,
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
             'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
             'Y', 'Z', '<',
             '_'])

    def test_alphabet_images(self):
        parameters_used = 'bcipy/parameters/parameters.json'
        parameters = load_json_parameters(parameters_used, value_cast=True)

        parameters['is_txt_sti'] = False
        parameters['path_to_presentation_images'] = ('bcipy/static/images/'
                                                     'rsvp_images/')

        alp = alphabet(parameters)

        self.assertNotEqual(
            alp,
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
             'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'Y', 'Z', '<',
             '_'])


class TestTrialReshaper(unittest.TestCase):

    def setUp(self):
        self.target_info = ['first_pres_target',
                            'target', 'nontarget', 'nontarget']
        self.timing_info = [1.001, 1.2001, 1.4001, 1.6001]
        # make some fake eeg data
        self.channel_number = 21
        tmp_inp = np.array([range(4000)] * self.channel_number)
        # Add some channel info
        tmp_inp[:, 0] = np.transpose(np.arange(1, 22, 1))
        self.eeg = tmp_inp
        self.channel_map = [1] * self.channel_number

    def tearDown(self):
        pass

    def test_trial_reshaper_calibration(self):
        (reshaped_trials, labels,
         num_of_seq, trials_per_sequence) = trial_reshaper(
            trial_target_info=self.target_info,
            timing_info=self.timing_info, filtered_eeg=self.eeg,
            fs=256, k=2, mode='calibration', channel_map=self.channel_map)

        self.assertTrue(
            len(reshaped_trials) == self.channel_number,
            f'len is {len(reshaped_trials)} not {self.channel_number}')

        # Since there are three trials of interest,
        # assert each channel has that information
        self.assertTrue(len(reshaped_trials[0]) == 3)

    def test_trial_reshaper_copy_phrase(self):
        pass


if __name__ == '__main__':
    unittest.main()
