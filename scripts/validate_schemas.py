import verde.verde_utils as vu
import os
import urllib3

meta_schema_file = '../schemas/local_verde_meta_schema.json'
asc_domain_schema_file = '../schemas/local_verde_asc_domain_schema.json'
asc_domain_mapping_schema_file = '../schemas/local_verde_asc_domain_mapping_schema.json'
test_input_mapping_file = '../asc_data/processed/set_00/AFR_T1_ASCOF_1A_mapping.json'


if __name__ == "__main__":
    os.environ["CURL_CA_BUNDLE"] = ""  # disable SSL verification because city certificate is not trusted
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # ... and suppress the warnings

    logging = vu.configure_logger('json_validate.log')

    vu.validate_json_doc(asc_domain_schema_file, meta_schema_file)
    vu.validate_json_doc(test_input_mapping_file, asc_domain_mapping_schema_file)




