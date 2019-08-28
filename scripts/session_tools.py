"""Tools for viewing and debugging session.json data"""

import contextlib
# prevents pygame from outputting to the console on import.
with contextlib.redirect_stdout(None):
    import pygame
import json
import sqlite3
import os
import pandas as pd
from collections import Counter

from bcipy.helpers.load import load_json_parameters
from bcipy.helpers.task import alphabet


def session_data(data_dir: str, alp=None):
    """Returns a dict of session data transformed to map the alphabet letter
    to the likelihood when presenting the evidence. Also removes attributes
    not useful for debugging."""

    # Get the alphabet based on the provided parameters (txt or icon).
    parameters = load_json_parameters(
        os.path.join(data_dir, "parameters.json"), value_cast=True)
    if parameters.get('is_txt_sti', False):
        parameters['is_txt_stim'] = parameters['is_txt_sti']

    if not alp:
        alp = alphabet(parameters=parameters)

    session_path = os.path.join(data_dir, "session.json")
    with open(session_path, 'r') as json_file:
        data = json.load(json_file)
        data['copy_phrase'] = parameters['task_text']
        for epoch in data['epochs'].keys():
            for trial in data['epochs'][epoch].keys():
                likelihood = dict(
                    zip(alp, data['epochs'][epoch][trial]['likelihood']))

                # Remove unused properties
                unused = ['eeg_len', 'timing_sti', 'triggers', 'target_info', 'copy_phrase']
                removeProps(data['epochs'][epoch][trial], unused)

                data['epochs'][epoch][trial]['stimuli'] = data['epochs'][
                    epoch][trial]['stimuli'][0]

                # Associate letters to values
                data['epochs'][epoch][trial]['lm_evidence'] = dict(
                    zip(alp, data['epochs'][epoch][trial]['lm_evidence']))
                data['epochs'][epoch][trial]['eeg_evidence'] = dict(
                    zip(alp, data['epochs'][epoch][trial]['eeg_evidence']))
                data['epochs'][epoch][trial]['likelihood'] = likelihood

                # Display the 5 most likely values.
                data['epochs'][epoch][trial]['most_likely'] = dict(
                    Counter(likelihood).most_common(5))

        return data


def session_db(data_dir: str, db_name='session.db', alp=None):
    """Writes a relational database (sqlite3) of session data that can
    be used for exploratory analysis.

    Parameters:
    -----------
        data_dir - directory with the session.json data (and parameters.json)
        db_name - name of database to write; defaults to session.db
        alp - optional alphabet to use

    Returns:
    --------
        Creates a sqlite3 database and returns a pandas dataframe of the
        evidence table for use within a repl.

    Schema:
    ------
    trial:
        - id: int
        - target: str

    evidence:
        - trial integer (0-based)
        - sequence integer (0-based)
        - letter text (letter or icon)
        - lm real (language model probability for the trial; same for every
            sequence and only considered in the cumulative value during the
            first sequence)
        - eeg real (likelihood for the given sequence; a value of 1.0 indicates
            that the letter was not presented)
        - cumulative real (cumulative likelihood for the trial thus far)
        - seq_position integer (sequence position; null if not presented)
        - is_target integer (boolean; true(1) if this letter is the target)
        - presented integer (boolean; true if the letter was presented in 
            this sequence)
        - above_threshold (boolean; true if cumulative likelihood was above
            the configured threshold)
    """
    # Get the alphabet based on the provided parameters (txt or icon).
    parameters = load_json_parameters(os.path.join(data_dir,
                                                   "parameters.json"),
                                      value_cast=True)
    if parameters.get('is_txt_sti', False):
        parameters['is_txt_stim'] = parameters['is_txt_sti']
    if not alp:
        alp = alphabet(parameters=parameters)

    session_path = os.path.join(data_dir, "session.json")
    with open(session_path, 'r') as json_file:
        data = json.load(json_file)

        # Create database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE trial (id integer, target text)')
        cursor.execute(
            'CREATE TABLE evidence (trial integer, sequence integer, letter text, lm real, eeg real, cumulative real, seq_position integer, is_target integer, presented integer, above_threshold)'
        )
        conn.commit()

        for epoch in data['epochs'].keys():
            for i, trial in enumerate(data['epochs'][epoch].keys()):
                if i == 0:
                    # create record for the trial
                    conn.executemany(
                        'INSERT INTO trial VALUES (?,?)',
                        [(int(epoch),
                          data['epochs'][epoch][trial]['target_letter'])])

                lm_ev = dict(
                    zip(alp, data['epochs'][epoch][trial]['lm_evidence']))
                cumulative_likelihoods = dict(
                    zip(alp, data['epochs'][epoch][trial]['likelihood']))

                ev_rows = []
                for letter, prob in zip(
                        alp, data['epochs'][epoch][trial]['eeg_evidence']):
                    seq_position = None
                    if letter in data['epochs'][epoch][trial]['stimuli']:
                        seq_position = data['epochs'][epoch][trial][
                            'stimuli'].index(letter)
                    is_target = 1 if data['epochs'][epoch][trial][
                        'target_letter'] == letter else 0
                    cumulative = cumulative_likelihoods[letter]
                    above_threshold = cumulative >= parameters[
                        'decision_threshold']
                    ev = (int(epoch), int(trial), letter, lm_ev[letter], prob,
                          cumulative, seq_position, is_target,
                          seq_position is not None, above_threshold)
                    ev_rows.append(ev)

                conn.executemany(
                    'INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?)',
                    ev_rows)
                conn.commit()
        dataframe = pd.read_sql_query("SELECT * FROM evidence", conn)
        conn.close()
        return dataframe


def removeProps(data, proplist):
    for prop in proplist:
        if prop in data:
            data.pop(prop)

def main(data_dir: str, alphabet: str):
    """Transforms the session.json file in the given directory and prints the
    resulting json."""
    print(json.dumps(session_data(data_dir, alphabet), indent=4))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Opens session.json file for analysis.")

    parser.add_argument(
        '-p', '--path', help='path to the data directory', default=None)
    parser.add_argument('--db', help='create sqlite database', default=False)
    parser.add_argument(
        '-a', '--alphabet', help='alphabet (comma-delimited string of items)', default=None)

    args = parser.parse_args()
    path = args.path
    if not path:
        from tkinter import Tk
        from tkinter import filedialog

        root = Tk()
        root.withdraw()
        path = filedialog.askdirectory(
            parent=root, initialdir="/", title='Please select a directory')

    alp = None
    if args.alphabet:
        alp = args.alphabet.split(",")

    if args.db:
        session_db(path, alp=alp)
    else:
        main(path, alp)
