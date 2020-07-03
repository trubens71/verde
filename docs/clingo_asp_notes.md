# Notes on clingo arguments and asp files

clingo /Users/trubens/verde_repos/draco/draco/../asp/define.lp
/Users/trubens/verde_repos/draco/draco/../asp/generate.lp
/Users/trubens/verde_repos/draco/draco/../asp/hard.lp
/Users/trubens/verde_repos/draco/draco/../asp/hard-integrity.lp
/Users/trubens/verde_repos/draco/draco/../asp/soft.lp
/Users/trubens/verde_repos/draco/draco/../asp/weights.lp
/Users/trubens/verde_repos/draco/draco/../asp/assign_weights.lp
/Users/trubens/verde_repos/draco/draco/../asp/optimize.lp
/Users/trubens/verde_repos/draco/draco/../asp/output.lp
tmp_cat.lp
--outf=2 --quiet=1,2,2

define.lp (121 lines)

- has definitions of chart constructs e.g. marktype
- orientation alludes to understanding of dependent and independent variables

generate.lp (33 lines)

- limits encoding channels to 5
- channel and type are mandatory
- aggregation, binning etc not mandatory
- only one mark type

hard.lp (208 lines)

- "Expressiveness and Well-Formedness Constraints"
- ... within encodings
- ... across encodings and between encodings and marks
- e.g. Can only use log with quantitative

hard-integrity.lp (3 lines)

- just seems to say that hard rules can have 1,2 or 3 arguments.

===== THIS LOOKS LIKE THE ZONE TO PLAY IN ========

soft.lp (469 lines)

- preferences
- e.g. Prefer not to use non-positional channels until all positional channels are used
- Interesting: avoid high cardinality on x or column as it causes horizontal scrolling

weights.lp (165)

- constants, between 0 and 30
- e.g. #const aggregate_weight = 1. #const bin_weight = 2. seems to suggest aggregation is preferable to binning

assign_weights.lp (151 lines generated)

- e.g. soft_weight(type_q,type_q_weight).
- appears to map from soft.lp to weights.lp

  Example for one preference:

  soft.lp:
  % @constraint Prefer not to use log scale.
  soft(log,E) :- log(E).

  weights.lp:
    const log_weight = 1.

  assign_weights.lp:
  soft_weight(log,log_weight).

===================================================

optimize.lp (1 line)

- No idea what this does. Says "Minimize the feature weight"
- minimize { W,F,Q: soft*weight(F,W), soft(F,Q); #inf,F,Q: soft(F,Q), not soft_weight(F,*); #inf,F: hard(F); #inf,F,Q: hard(F,Q); #inf,F,Q1,Q2: hard(F,Q1,Q2) }.

output.lp (17 lines)

- which variables to output
- e.g. #show mark/1.
