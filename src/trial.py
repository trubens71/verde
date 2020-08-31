import logging
import os
import yaml


class Trial:
    """
    Data structure to hold the trial and experiment config.
    Only logic is to copy the global settings into each experiment.
    """

    def __init__(self, directory, config_file):

        self.directory = directory
        self.config_file = directory + '/' + config_file

        if not os.path.isfile(self.config_file):
            logging.fatal(f'config file {self.config_file} not found')

        with open(self.config_file) as f:
            self._raw_config = yaml.load(f, Loader=yaml.FullLoader)

        self.trial_id = self._raw_config['trial_id']
        self.trial_desc = self._raw_config['trial_desc']
        self.global_trial_settings = self._raw_config['global_trial_settings']
        self.experiments = self._raw_config['experiments']

        # duplicate attributes and copy across the global settings to each experiment
        for exp in self.experiments:
            exp['trial_id'] = self.trial_id
            exp['trial_desc'] = self.trial_desc
            exp['directory'] = self.directory
            exp['id'] = f"{self.trial_id}.{exp['experiment_id']}"
            for global_k, global_v in self.global_trial_settings.items():
                if global_k in exp:
                    logging.warning(f"{global_k}={global_v} overriding {exp[global_k]} in {exp['experiment_id']}")
                exp[global_k] = global_v



