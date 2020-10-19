import logging


def rule_04_ordinal(context, schema_file, input_file, mapping_json, query_fields):
    logging.warning('rule 04 not yet implemented')


"""
rule development
% verde
fieldcolorscheme("Gross_Total_Expenditure_x1000", "{\"scheme\": \"oranges\"}").
fieldmarkcolor("LA_name","{\"color\": \"black\"}").
fieldmarkcolor("Geography_code","{\"color\": \"gray\"}").
fieldmarkcolor("Region_name","{\"color\": \"blue\"}").
fieldcolorscheme("Setting", "{\"scheme\": \"pastel1\"}").

% first case: color channel is used and we have a scheme for the encoding field.
verde_color_enc_scheme(V,E,F,CS) :- fieldcolorscheme(F,CS), field(V,E,F), channel(V,E,color).

% second case: if first case not applied, and we have non-aggregated field encoding for which there is a schema...
verde_color_double_enc_scheme(V,E,F,CS) :- not verde_color_enc_scheme(_,_,_,_), field(V,E,F), not aggregate(V,E,_), discrete(V,E), fieldcolorscheme(F,CS).

% third case: if first two cases does not apply but we have an appropriate mark color
verde_mark_color_choices(V,CO) :- not verde_color_enc_scheme(_,_,_,_), not verde_color_double_enc_scheme(_,_,_,_), view(V), fieldmarkcolor(F,CO), fieldtype(F,FT), FT != "number", cardinality(F,CA), num_rows(NR), CA = NR.
% choose only one
1 { verde_color_mark(V,CO): verde_mark_color_choices(V,CO)} 1 :- verde_mark_color_choices(_,_).

#show verde_color_enc_scheme/4.
#show verde_color_double_enc_scheme/4.
#show verde_color_mark/2.

soft(verde_color_enc_scheme,V,E) :- verde_color_enc_scheme(V,E,F,CS).
soft(verde_color_double_enc_scheme,V,E) :- verde_color_double_enc_scheme(V,E,F,CS).
soft(verde_color_mark,V,CO) :- verde_color_mark(V,CO).

#const verde_color_enc_scheme_weight = 0.
#const verde_color_double_enc_scheme_weight = 0.
#const verde_color_mark_weight = 0.

soft_weight(verde_color_enc_scheme, verde_color_enc_scheme_weight).
soft_weight(verde_color_double_enc_scheme, verde_color_double_enc_scheme_weight).
soft_weight(verde_color_mark, verde_color_mark_weight).

"""
"""
Draco colour rules.

They all relate to use of the colour channel, therefore conclude that
colour and schema choices are deferred to vega-lite

% @constraint Prefer not to use high cardinality nominal for color.
soft(high_cardinality_nominal_color,V,E) :- type(V,E,nominal), channel(V,E,color), enc_cardinality(V,E,C), C > 10.
#const high_cardinality_nominal_color_weight = 10.

% @constraint Continuous on color channel.
soft(continuous_color,V,E) :- channel(V,E,color), continuous(V,E).
#const continuous_color_weight = 10.

% @constraint Ordered on color channel.
soft(ordered_color,V,E) :- channel(V,E,color), discrete(V,E), not type(V,E,nominal).
#const ordered_color_weight = 8.

% @constraint Nominal on color channel.
soft(nominal_color,V,E) :- channel(V,E,color), type(V,E,nominal).
#const nominal_color_weight = 6.

There are other colour rules related to entropy, interesting, value/summary task, which we do not encounter.
Those are still concerned with encoding the colour channel.
"""