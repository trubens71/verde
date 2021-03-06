"""
experiment.py

Class to hold the experiment configuration and orchestrate its execution.
"""

import logging
import src.utils as vutils
import src.draco_proxy as vdraco
import src.domain_rules as vrules
import src.results as vresults
import src.compare as vcompare
import json
from deepmerge import always_merger


class Experiment:

    def __init__(self, trial, exp):
        """
        Construct an experiment
        :param trial: the parent trial object from which we inherit some values
        :param exp: the config details for this experiment
        """

        self.verde_meta_schema = None
        self.domain_schema = None
        self.domain_mapping_schema = None
        self.input_data_file = None
        self.input_mapping_file = None
        self.query = None
        self.query_fields = None
        self.execute = None
        self.baseline_schema_query_lp = None
        self.verde_schema_query_lp = None
        self.draco_base_lp_dir = None
        self.baseline_vis_results = None
        self.baseline_vis_results_json = None
        self.num_models = None
        self.verde_vis_results = None
        self.verde_vis_results_json = None
        self.verde_base_lp_override_dir = None
        self.verde_rule_template_dir = None
        self.vega_lite_schema = None

        # create a composite id of trial and experiment
        self.id = f"{trial.trial_id}.{exp['experiment_id']}"
        logging.info(f'creating experiment {self.id}')

        # inherit some values from the trial for easier future referencing
        self.trial_id = trial.trial_id
        self.trial_desc = trial.trial_desc
        self.directory = trial.directory

        # override global trial config with any local values in experiment config
        trial_global_config = trial.global_config.deepcopy()
        for config_k, config_v in always_merger.merge(trial_global_config, exp).items():
            setattr(self, config_k, config_v)

    def run(self):

        """
        Run the experiment
        :return: None
        """

        logging.info(f'*** running experiment {self.id} ***')

        # clear out temp files from previous runs based on id and directory
        vutils.delete_temp_files(self.directory, self.id)

        # validate the domain schema against the verde meta schema
        if self.execute.validate_domain_schema.do:
            if not vutils.validate_json_doc(self.domain_schema, self.verde_meta_schema):
                exit(1)
        else:
            logging.warning('validate_domain_schema json validation turned off in trial config')

        # validate the input mapping file against the domain schema.
        # note that this involves $refs to the domain model so needs the domain model to be publicly available on github
        if self.execute.validate_input_file_mapping.do:
            if not vutils.validate_json_doc(self.input_mapping_file, self.domain_mapping_schema):
                exit(1)
        else:
            logging.warning('validate_input_file_mapping json validation turned off in trial config')

        # Clingo does not like spaces and special chars in atom names so we need to fix the input csv file
        # and the file that maps it to the domain model.
        if self.execute.fix_input_file_column_names.do:
            self.input_data_file, self.input_mapping_file, self.query = \
                vutils.fix_column_headings(self.input_data_file, self.input_mapping_file, self.id, self.query,
                                           self.directory + '/data', )
        else:
            logging.warning('fix_input_file_column_names turned off in trial config')

        if self.execute.create_baseline_schema_query_lp.do:
            self.baseline_schema_query_lp, self.query_fields = \
                vdraco.get_baseline_schema_query_lp(self.input_data_file,
                                                    self.query,
                                                    self.id,
                                                    self.directory,
                                                    self.execute.create_baseline_schema_query_lp.write_lp)
        else:
            logging.warning('create_baseline_schema_query_lp turned off in trial config')

        if self.execute.create_verde_rules_lp.do:
            self.verde_schema_query_lp = vrules.create_verde_rules_lp(self.domain_schema,
                                                                      self.input_data_file,
                                                                      self.input_mapping_file,
                                                                      self.query_fields,
                                                                      self.id,
                                                                      self.directory,
                                                                      self.execute.create_verde_rules_lp,
                                                                      self.baseline_schema_query_lp,
                                                                      self.verde_rule_template_dir)
        else:
            logging.warning('create_verde_rules_lp turned off in trial config')

        if self.execute.create_baseline_visualisations.do and self.baseline_schema_query_lp:
            self.baseline_vis_results, self.baseline_vis_results_json = \
                vresults.get_vis_results(self.id, self.directory, self.input_data_file,
                                         self.baseline_schema_query_lp,
                                         self.draco_base_lp_dir,
                                         num_models=self.num_models,
                                         label='baseline',
                                         write_lp=self.execute.create_baseline_visualisations.write_lp)
        else:
            logging.warning('cannot get baseline visualisations due to trial config conflict')

        if self.execute.create_verde_visualisations.do and self.verde_schema_query_lp:
            self.verde_vis_results, self.verde_vis_results_json = \
                vresults.get_vis_results(self.id, self.directory, self.input_data_file,
                                         self.verde_schema_query_lp,
                                         self.draco_base_lp_dir,
                                         override_lp_dir=self.verde_base_lp_override_dir,
                                         num_models=self.num_models,
                                         label='verde',
                                         write_lp=self.execute.create_verde_visualisations.write_lp)
        else:
            logging.warning('cannot get verde visualisations due to trial config conflict')

        result_sets = []
        set_labels = []
        if self.execute.create_vegalite_concat.do:
            if self.baseline_vis_results_json and self.verde_vis_results_json:
                result_sets = [self.baseline_vis_results_json, self.verde_vis_results_json]
                set_labels = ['baseline', 'verde']
            elif self.baseline_vis_results_json:
                result_sets = [self.baseline_vis_results_json]
                set_labels = ['baseline']
            elif self.verde_vis_results_json:
                result_sets = [self.verde_vis_results_json]
                set_labels = ['verde']
            else:
                logging.warning(
                    'cannot create concatenated baseline and verde vega-lite spec due to trial config conflict')
            if result_sets and set_labels:
                vresults.make_vegalite_concat(self.id, self.directory, result_sets,
                                              set_labels, self.vega_lite_schema)

        if self.execute.compare_baseline_verde.do and self.baseline_vis_results_json and self.verde_vis_results_json:
            vcompare.compare_baseline_to_verde(self.id, self.directory,
                                               self.baseline_vis_results_json, self.verde_vis_results_json)
        else:
            logging.warning('cannot compare verde to baseline result sets due to trial config conflict')
