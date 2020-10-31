"""
trial.py

Class to hold the trial data and loads its experiments.
"""

import logging
import os
import yaml
from src.experiment import Experiment
import src.utils as vutils
from addict import Dict

TRIAL_YAML = 'trial.yaml'  # required name of configuration file defining a trial and its experiments
TRIAL_SCHEMA = '../schemas/verde_trial_schema.json'  # json schema to validate TRIAL_YAML against


class Trial:

    """
    Data structure to hold the trial config and its experiment objects
    """

    def __init__(self, directory):
        """
        Construct the trial and its experiment objects
        :param directory: for the trial
        :param config_file: name of the config file expected in the directory
        """

        self.directory = directory
        self.config_file = os.path.join(self.directory, TRIAL_YAML)

        if not os.path.isdir(directory):
            logging.fatal(f'trial directory {self.directory} not found')
            exit(1)

        if not os.path.isfile(self.config_file):
            logging.fatal(f'config file {self.config_file} not found')
            exit(1)

        if not vutils.validate_json_doc(self.config_file, TRIAL_SCHEMA):
            logging.fatal(f'{self.config_file} failed validation against {TRIAL_SCHEMA}')

        with open(self.config_file) as f:
            self._raw_config = Dict(yaml.load(f, Loader=yaml.FullLoader))

        logging.info(f'loading trial config from {self.config_file}')

        self.trial_id = self._raw_config['trial_id']
        self.trial_desc = self._raw_config['trial_desc']
        self.global_config = self._raw_config['global_config']
        self.regression_test = self._raw_config['regression_test']

        # create the experiment objects
        self.experiments = []
        for exp in self._raw_config['experiments']:
            self.experiments.append(Experiment(self, exp))

    def exec_regression_test(self):

        """
        Will compare output files against a regression test baseline
        :return:
        """

        if self.regression_test['do']:
            vutils.regression_test(self.directory)
        else:
            logging.warning('regression test disabled in config')