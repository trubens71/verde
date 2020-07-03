#!/bin/zsh
# Run a data source through data2schema and schema2asp
# Run a basic compassQL query through cql2asp
# Concatenate results into a single logic program,
# optionally add in a verde rules then run through Draco.

DRACO_ROOT=/Users/trubens/verde_repos/draco
DATA_ROOT=/Users/trubens/verde_repos/verde/asc_data/processed/set_00

DATA_FILE=AFR_T1_ASCOF_1A_fixhdr.json
QUERY_FILE=AFR_T1_ASCOF_1A.cql.json
VERDE_RULE_FILE=AFR_T1_ASCOF_1A_rule1_v2.lp
VL_FILE=AFR_T1_ASCOF_1A.vl.json

ADD_VERDE_RULE=0
TMP_CAT='tmp_cat.lp'

while getopts 'd:q:vr:o:' c
do
  case $c in
    d) DATA_FILE=${OPTARG} ;;
    q) QUERY_FILE=${OPTARG} ;;
    v) ADD_VERDE_RULE=1;;
    r) VERDE_RULE_FILE=$OPTARG ;;
		o) VL_FILE=$OPTARG ;;
    *) ;;
  esac
done

echo Processing "${DATA_FILE}"

# shellcheck disable=SC2002
cat ${DATA_ROOT}/"$DATA_FILE" | ${DRACO_ROOT}/js/bin/data2schema |\
	${DRACO_ROOT}/js/bin/schema2asp > "${DATA_FILE}".lp
echo Written data schema ASP to "${DATA_FILE}".lp

# shellcheck disable=SC2002
cat "${QUERY_FILE}" | ${DRACO_ROOT}/js/bin/cql2asp > "${QUERY_FILE}".lp
echo Written query ASP to "${QUERY_FILE}".lp

if [ ${ADD_VERDE_RULE} -ne 0 ]
then
	echo Adding verde rule file to lp: "${VERDE_RULE_FILE}"
	cat "${DATA_FILE}".lp "${QUERY_FILE}".lp "${VERDE_RULE_FILE}" > ${TMP_CAT}
else
	echo Not adding verde rule file to lp
	cat "${DATA_FILE}".lp "${QUERY_FILE}".lp > ${TMP_CAT}
fi

echo Executing Draco with ${TMP_CAT} to "${VL_FILE}"
draco ${TMP_CAT} --out "${VL_FILE}"

echo Here is the VL spec...
cat "${VL_FILE}"
