import pandas as pd
import logging
import os
import sys
import re
import json
import jsonschema
import itertools
from draco.helper import read_data_to_asp
from draco.js import cql2asp
from draco.cli import draco_main_argv


def fix_csv_column_headers(csv_file_path):
    """
    Clingo doesn't like spaces, brackets or hyphens in variable names,
    so we need to do a bit of regex substitution on our input csv files.
    This means that our mapping docs from data to schema will need translation,
    so we maintain a mapping from old column headers to new.
    :param csv_file_path: path to input file
    :return: fixed_csv_path and a dict of old to new column names
    """

    fixed_csv_file_path = os.path.splitext(csv_file_path)[0] + '_colfix.csv'
    logging.info('Fixing csv columns headers {} to {}'.format(csv_file_path, fixed_csv_file_path))

    df = pd.read_csv(csv_file_path)
    old_columns = df.columns

    # replace non-alpha/digit with underscores, tidy up multiple and leading/trailing underscores
    df.rename(columns=lambda x: re.sub('[^A-Za-z0-9]', '_', x), inplace=True)
    df.rename(columns=lambda x: re.sub('_{2,}', '_', x), inplace=True)
    df.rename(columns=lambda x: re.sub('^_|_$', '', x), inplace=True)
    df.to_csv(fixed_csv_file_path, index=False)

    column_map = dict(zip(old_columns, df.columns))
    column_mapping_file_path = os.path.splitext(csv_file_path)[0] + '_colfixmap.json'

    with open(column_mapping_file_path, 'w') as f:
        logging.info('Saving column header mapping to {}'.format(column_mapping_file_path))
        json.dump(column_map, f)

    return fixed_csv_file_path, column_map


def create_schema_asp(input_file_path):

    """
    Take either a csv or a json input data file and run it through data2schema and schema2asp
    to create an ASP of facts that describe the input data
    :param input_file_path: a csv or json file
    :return: file path to a Draco schema asp, and a list of the asp rules
    """
    logging.info('Creating schema asp from {}'.format(input_file_path))
    file_root, file_ext = os.path.splitext(input_file_path)
    schema_file_path = file_root + '_schema_asp.lp'
    schema_asp = read_data_to_asp(input_file_path)  # Draco helper function
    write_list_to_file(schema_asp, schema_file_path, 'schema asp')
    return schema_file_path, schema_asp


def create_cql_query_asp(input_file_path):

    """
    Take a CompassQL query file and create an asp
    :param input_file_path:
    :return: asp file path and asp list
    """

    logging.info('Creating query asp from {}'.format(input_file_path))
    file_root, file_ext = os.path.splitext(input_file_path)
    query_file_path = file_root + '_asp.lp'

    with open(input_file_path, 'r') as f:
        cql_query_json = json.load(f)

    query_asp = cql2asp(cql_query_json)  # Draco helper function
    write_list_to_file(query_asp, query_file_path, 'query asp')
    return query_file_path, query_asp


def create_verde_rule_asp(input_file_path):
    """
    Create verde rule asp. Currently a file drive stub
    :param input_file_path:
    :return: asp list
    """

    logging.info('Reading verde rule asp from {}'.format(input_file_path))

    with open(input_file_path, 'r') as f:
        verde_rule_asp = f.readlines()

    return verde_rule_asp


def run_trial(asp_list, prefix, postfix):
    """
    Run draco on with the passed in asp
    :param asp_list: a list of asps
    :param prefix: where to put lp and vl files
    :param postfix: trial reference number
    :return:
    """

    asp = list(itertools.chain(*asp_list))
    input_file_path = prefix + '.{}.lp'.format(postfix)
    write_list_to_file(asp, input_file_path, 'full asp')

    output_file_path = prefix + '.{}.vl.json'.format(postfix)
    draco_main_argv([input_file_path, '--out', output_file_path])


def validate_json_doc(doc_file_path, schema_file_path=None):
    """
    Validate a JSON document against a schema
    :param doc_file_path:
    :param schema_file_path:
    :return: success
    """
    logging.info('Validating {} against {}'.format(doc_file_path, schema_file_path))

    if schema_file_path:
        with open(schema_file_path, 'r') as f:
            schema = json.load(f)
    else:
        schema = jsonschema.Draft7Validator.META_SCHEMA

    with open(doc_file_path, 'r') as f:
        doc = json.load(f)

    success = False

    try:
        jsonschema.Draft7Validator(schema).validate(doc)
    except jsonschema.ValidationError as ex:
        logging.error(ex.message)
    else:
        logging.info('successfully validated')
        success = True

    return success


def write_list_to_file(content_list, input_file_path, desc=''):
    """
    write a list to file
    :param desc: description for logging
    :param content_list: a list of strings
    :param input_file_path:
    :return: null
    """
    logging.info('Writing {} to {}'.format(desc, input_file_path))
    with open(input_file_path, 'w') as f:
        for line in content_list:
            f.write('{}\n'.format(line))


def configure_logger(log_file, level=logging.INFO):
    """
    Creates a logging instance which writes to file and stdout
    :param log_file: path to logfile
    :param level: logging.DEBUG, logging.INFO (default)
    :return: logging instance
    """
    # Clear out old loggers (for Jupyter use when the handlers stay in scope between runs)
    for h in logging.getLogger('').handlers:
        logging.getLogger('').removeHandler(h)
    # configure logging to write to file and stdout with a nice format and
    # for info and above messages
    fh = logging.StreamHandler(sys.stdout)
    ch = logging.FileHandler(log_file, mode='w')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)
    logging.getLogger('').setLevel(level)
    return logging