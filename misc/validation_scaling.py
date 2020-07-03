import pandas as pd
from jsonschema import validate
import json
from datetime import datetime


def prepare(input_file, scale=1):
    print('preparing {} with scale {}'.format(input_file, scale))
    df = pd.read_csv(input_file)
    print('Input file has {} records'.format(len(df)))
    output_file = input_file + '_' + str(scale) + '.json'
    df_out = df
    for i in range(scale-1):
        df_out = pd.concat([df_out, df], axis=0)
    print('Output file has {} records'.format(len(df_out)))
    df_out.to_json(output_file, orient='records')
    return output_file


def validate_input(input_file, schema_file):
    print('validating {} against {}'.format(input_file,schema_file))
    with open(input_file) as in_f:
        json_obj = json.load(in_f)
    with open(schema_file) as in_s:
        schema_obj = json.load(in_s)
    res = validate(instance=json_obj, schema=schema_obj)
    print(res)

# WARNING - This won't work in situ here as needs csv data and a JSON schema
# WARNING - This scales horribly in duplicating data with pandas
if __name__ == "__main__":
    json_file = prepare('AFR_T1_ASCOF_1A.csv',1000)
    start = datetime.now()
    validate_input(json_file, 'AFR_T1_ASCOF_1A_schema.json')
    print((datetime.now() - start).total_seconds())
