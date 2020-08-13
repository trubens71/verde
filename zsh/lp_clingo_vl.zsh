#!/bin/zsh

INPUT_FILE="${argv[1]}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "input file $FILE not found."
    exit 1
fi

BASE=$(basename "${INPUT_FILE}" .lp)
GROUND_FILE="${BASE}_grnd.lp"
ANSWER_FILE="${BASE}_ans.json"

echo running "$INPUT_FILE" through gringo to "$GROUND_FILE"
if gringo --text "$INPUT_FILE" > "$GROUND_FILE"; then
  echo success
else
  exit 1
fi

echo running "$INPUT_FILE" through clingo to "$ANSWER_FILE"
clingo --outf=2 --quiet=0,0,2 "$INPUT_FILE" > "$ANSWER_FILE"

echo running "$INPUT_FILE" and "$ANSWER_FILE" through inspect_multi_models.py
if inspect_multi_models.py -l "$INPUT_FILE" -a "$ANSWER_FILE" -v vl; then
  echo success
else
  exit 1
fi
