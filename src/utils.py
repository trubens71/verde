import logging
import sys
import json
import jsonschema
import os
import pandas as pd
import re
import glob


def fix_column_headings(input_csv_file, input_map_file, id, query, output_dir, postfix='_colfix'):

    """
    Clingo does not like special chars in atom names so we need to get rid of spaces and special chars.
    We have to do that in our input csv file, its mapping to the domain and fields referenced in the query.
    A shame we repeat the same regex patterns 3 times, but the input format is different in each case.
    :param id: experiment id for prefix
    :param input_csv_file:
    :param input_map_file:
    :param query:
    :param output_dir:
    :param postfix:
    :return: output_csv_file, output_map_file, query
    """
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    prefix = id + '_'

    # process the input csv file
    output_csv_file = os.path.basename(input_csv_file)
    output_csv_file = prefix + os.path.splitext(output_csv_file)[0] + postfix + '.csv'
    output_csv_file = os.path.join(output_dir, output_csv_file)
    logging.info(f'fixing csv column headers (special chars disallowed by clingo) in {input_csv_file} to {output_csv_file}')
    df = pd.read_csv(input_csv_file)
    # replace non-alpha/digit with underscores, tidy up multiple and leading/trailing underscores.
    df.rename(columns=lambda x: re.sub('[^A-Za-z0-9]', '_', x), inplace=True)
    df.rename(columns=lambda x: re.sub('_{2,}', '_', x), inplace=True)
    df.rename(columns=lambda x: re.sub('^_|_$', '', x), inplace=True)
    df.to_csv(output_csv_file, index=False)

    # process the input mapping file in a similar same way
    output_map_file = os.path.basename(input_map_file)
    output_map_file = prefix + os.path.splitext(output_map_file)[0] + postfix + '.json'
    output_map_file = os.path.join(output_dir, output_map_file)
    logging.info(f'fixing map file column names in {input_map_file} to {output_map_file}')
    # read input
    with open(input_map_file) as f:
        j = json.load(f)
    # replace non-alpha/digit with underscores, tidy up multiple and leading/trailing underscores.
    for i, column in enumerate(j):
        column_name = column['column_name']
        column_name = re.sub('[^A-Za-z0-9]', '_', column_name)
        column_name = re.sub('_{2,}', '_', column_name)
        column_name = re.sub('^_|_$', '', column_name)
        j[i]['column_name'] = column_name
    # write output
    with open(output_map_file, 'w') as f:
        json.dump(j, f)

    # same again for our query terms
    logging.info('fixing query field names')
    for i, query_term in enumerate(query):
        field_args = re.match(r'field\((.*)\)', query_term)
        field_args = field_args[1].split(',')
        field_args[0] = re.sub('[^A-Za-z0-9]', '_', field_args[0])
        field_args[0] = re.sub('_{2,}', '_', field_args[0])
        field_args[0] = re.sub('^_|_$', '\'', field_args[0])
        query[i] = f"field({','.join(field_args)})"

    return output_csv_file, output_map_file, query


def validate_json_doc(doc_file_path, schema_file_path=None):
    """
    Validate a JSON document against a schema
    :param doc_file_path:
    :param schema_file_path:
    :return: success
    """
    logging.info('validating {} against {}'.format(doc_file_path, schema_file_path))

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


def write_list_to_file(content_list, output_file, desc=''):
    """
    write a list to file
    :param desc: description for logging
    :param content_list: a list of strings
    :param output_file:
    :return: null
    """
    logging.info(f'writing {desc} to {output_file}')
    with open(output_file, 'w') as f:
        for line in content_list:
            f.write('{}\n'.format(line))


def delete_temp_files(directory, prefix):

    logging.info(f'deleting experiment output files {prefix}* recursively from {directory}')
    glob_path = f'{directory}/**/{prefix}*'
    files = glob.glob(glob_path, recursive=True)

    for file in files:
        logging.debug(f'deleting {file}')
        os.remove(file)


def configure_logger(log_file, level=logging.INFO, show_mod_func=False):
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
    if show_mod_func:
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(module)s.%(funcName)s : %(message)s',
                                      "%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s', "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)
    logging.getLogger('').setLevel(level)
    return logging
