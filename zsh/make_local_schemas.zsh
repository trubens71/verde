#!/bin/zsh

SCHEMA_DIR='../schemas'
REMOTE_URI='https://smcse.city.ac.uk/student/aczd178/verde/schema/verde_'
LOCAL_URI='file:/Users/trubens/verde_repos/verde/schemas/local_verde_'

for SCHEMA_FILE_PATH in `ls ${SCHEMA_DIR}/verde_*_schema.json`
do
  SCHEMA_FILE=$SCHEMA_FILE_PATH:t
  LOCAL_SCHEMA_FILE_PATH="${SCHEMA_DIR}/local_${SCHEMA_FILE}"
  echo "Processing ${SCHEMA_FILE_PATH} to ${LOCAL_SCHEMA_FILE_PATH}"
  sed -e "s|${REMOTE_URI}|${LOCAL_URI}|g" "${SCHEMA_FILE_PATH}" > "${LOCAL_SCHEMA_FILE_PATH}"
done

