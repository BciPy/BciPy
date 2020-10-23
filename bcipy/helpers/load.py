from datetime import datetime
from tkinter import Tk
import numpy as np
import pandas as pd
import logging
from codecs import open as codecsopen
from json import load as jsonload
from shutil import copyfile
from pathlib import Path
import pickle

from tkinter.filedialog import askopenfilename, askdirectory

log = logging.getLogger(__name__)

DEFAULT_PARAMETERS_PATH = 'bcipy/parameters/parameters.json'

def _cast_parameters(parameters: dict) -> dict:
    """Cast to Value.

    Take in a parameters dictionary and coverts to a dictionary with type converted
        and extranous information removed.
    """
    new_parameters = {}
    for key, value in parameters.items():
        new_parameters[key] = cast_value(value)

    return new_parameters


def cast_value(value):
    """Cast Value.

    Takes in a value with a desired type and attempts to cast it to that type.
    """
    actual_value = str(value['value'])
    actual_type = value['type']

    try:
        if actual_type == 'int':
            new_value = int(actual_value)
        elif actual_type == 'float':
            new_value = float(actual_value)
        elif actual_type == 'bool':
            new_value = True if actual_value == 'true' else False
        elif actual_type == 'str' or 'path' in actual_type:
            new_value = str(actual_value)
        else:
            raise ValueError('Unrecognized value type')

    except Exception:
        raise ValueError(f'Could not cast {actual_value} to {actual_type}')

    return new_value

def copy_default_parameters(destination: str = 'bcipy/parameters/') -> str:
    """Creates a copy of the default configuration (parameters.json) to the
    given directory and returns the path

    Parameters:
    -----------
        destination: str - optional destination directory; default is the same
          directory as the default parameters.
    Returns:
    --------
        path to the new file.
    """
    now = datetime.now()
    month = str(now.month).rjust(2, "0")
    day = str(now.day).rjust(2, "0")
    hour = str(now.hour).rjust(2, "0")
    minute = str(now.minute).rjust(2, "0")
    second = str(now.second).rjust(2, "0")
    filename =  f'parameters_{now.year}-{month}-{day}_{hour}h{minute}m{second}s.json'

    path = str(Path(destination, filename))
    copyfile(DEFAULT_PARAMETERS_PATH, path)
    return path

def load_json_parameters(path: str, value_cast: bool = False) -> dict:
    """Load JSON Parameters.

    Given a path to a json of parameters, convert to a dictionary and optionally
        cast the type.

    Expects the following format:
    "fake_data": {
        "value": "true",
        "section": "bci_config",
        "readableName": "Fake Data Sessions",
        "helpTip": "If true, fake data server used",
        "recommended_values": "",
        "type": "bool"
        }

    PARAMETERS
    ----------
    :param: path: string path to the parameters file.
    :param: value_case: True/False cast values to specified type.
    """
    # loads in json parameters and turns it into a dictionary
    try:
        with codecsopen(path, 'r', encoding='utf-8') as f:
            parameters = []
            try:
                parameters = jsonload(f)

                if value_cast:
                    parameters = _cast_parameters(parameters)
            except ValueError:
                raise ValueError(
                    "Parameters file is formatted incorrectly!")

        f.close()

    except IOError:
        raise IOError("Incorrect path to parameters given! Please try again.")

    return parameters


def load_experimental_data() -> str:
    # use python's internal gui to call file explorers and get the filename
    try:
        Tk().withdraw()  # we don't want a full GUI
        filename = askdirectory()  # show dialog box and return the path

    except Exception as error:
        raise error

    log.debug("Loaded Experimental Data From: %s" % filename)
    return filename


def load_signal_model(filename: str = None):
    # use python's internal gui to call file explorers and get the filename

    if not filename:
        try:
            Tk().withdraw()  # we don't want a full GUI
            filename = askopenfilename()  # show dialog box and return the path

        # except, raise error
        except Exception as error:
            raise error

    # load the signal_model with pickle
    signal_model = pickle.load(open(filename, 'rb'))

    return (signal_model, filename)


def load_csv_data(filename: str = None) -> str:
    if not filename:
        try:
            Tk().withdraw()  # we don't want a full GUI
            filename = askopenfilename()  # show dialog box and return the path

        except Exception as error:
            raise error

    # get the last part of the path to determine file type
    file_name = filename.split('/')[-1]

    if 'csv' not in file_name:
        raise Exception(
            'File type unrecognized. Please use a supported csv type')

    return filename


def read_data_csv(folder: str, dat_first_row: int = 2,
                  info_end_row: int = 1) -> tuple:
    """ Reads the data (.csv) provided by the data acquisition
        Arg:
            folder(str): file location for the data
            dat_first_row(int): row with channel names
            info_end_row(int): final row related with daq. info
                where first row idx is '0'
        Return:
            raw_dat(ndarray[float]): C x N numpy array with samples
                where C is number of channels N is number of time samples
            channels(list[str]): channels used in DAQ
            stamp_time(ndarray[float]): time stamps for each sample
            type_amp(str): type of the device used for DAQ
            fs(int): sampling frequency
    """
    dat_file = pd.read_csv(folder, skiprows=dat_first_row)

    # Remove object columns (ex. BCI_Stimulus_Marker column)
    # TODO: might be better in use:
    # dat_file.select_dtypes(include=['float64'])
    numeric_dat_file = dat_file.select_dtypes(exclude=['object'])
    channels = list(numeric_dat_file.columns[1:])  # without timestamp column

    temp = numeric_dat_file.values
    stamp_time = temp[:, 0]
    raw_dat = temp[:, 1:temp.shape[1]].transpose()

    dat_file_2 = pd.read_csv(folder, nrows=info_end_row)
    type_amp = list(dat_file_2.axes[1])[1]
    fs = np.array(dat_file_2)[0][1]

    return raw_dat, stamp_time, channels, type_amp, fs


def load_txt_data() -> str:
    try:
        Tk().withdraw()  # we don't want a full GUI
        filename = askopenfilename()  # show dialog box and return the path
    except Exception as error:
        raise error

    file_name = filename.split('/')[-1]

    if 'txt' not in file_name:
        raise Exception(
            'File type unrecognized. Please use a supported text type')

    return filename
