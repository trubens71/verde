import logging
import os
import yaml
from src.experiment import Experiment
from addict import Dict


class Trial:
    """
    Data structure to hold the trial config and its experiment objects
    """

    def __init__(self, directory, config_file):
        """
        Construct the trial and its experiment objects
        :param directory: for the trial
        :param config_file: name of the config file expected in the directory
        """

        self.directory = directory
        self.config_file = directory + '/' + config_file

        if not os.path.isfile(self.config_file):
            logging.fatal(f'config file {self.config_file} not found')

        with open(self.config_file) as f:
            self._raw_config = Dict(yaml.load(f, Loader=yaml.FullLoader))

        logging.info(f'loading trial config from {self.config_file}')

        self.trial_id = self._raw_config['trial_id']
        self.trial_desc = self._raw_config['trial_desc']
        self.global_config = self._raw_config['global_config']

        # create the experiment objects
        self.experiments = []
        for exp in self._raw_config['experiments']:
            self.experiments.append(Experiment(self, exp))


