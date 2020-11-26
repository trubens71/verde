view(v_v).
num_rows(10).

fieldtype("region",string).
cardinality("region", 10).
fieldtype("region_code",string).
cardinality("region_code", 10).
fieldtype("zero_hr_contract_all_pct",number).
cardinality("zero_hr_contract_all_pct", 10).
fieldtype("zero_hr_contract_managerial_pct",number).
cardinality("zero_hr_contract_managerial_pct", 9).
fieldtype("zero_hr_contract_reg_prof_pct",number).
cardinality("zero_hr_contract_reg_prof_pct", 8).
fieldtype("zero_hr_contract_direct_care_pct",number).
cardinality("zero_hr_contract_direct_care_pct", 10).
fieldtype("zero_hr_contract_other_pct",number).
cardinality("zero_hr_contract_other_pct", 9).
fieldtype("vacancies_all_pct",number).
cardinality("vacancies_all_pct", 9).
fieldtype("vacancies_managerial_pct",number).
cardinality("vacancies_managerial_pct", 8).
fieldtype("vacancies_reg_prof_pct",number).
cardinality("vacancies_reg_prof_pct", 10).
fieldtype("vacancies_direct_care_pct",number).
cardinality("vacancies_direct_care_pct", 9).
fieldtype("vacancies_other_pct",number).
cardinality("vacancies_other_pct", 8).
fieldtype("QoL_all",number).
cardinality("QoL_all", 4).
fieldtype("QoL_male",number).
cardinality("QoL_male", 7).
fieldtype("QoL_female",number).
cardinality("QoL_female", 7).
fieldtype("QoL_18_64",number).
cardinality("QoL_18_64", 6).
fieldtype("QoL_65_over",number).
cardinality("QoL_65_over", 5).

encoding(v_v,e0).
encoding(v_v,e1).
:- not field(v_v,E,"region") : encoding(v_v,E).
:- not field(v_v,E,"QoL_all") : encoding(v_v,E).
:- field(v_v,E,"QoL_all"), not zero(v_v,E).

% --- verde rule 01 (causal relationships) ----------------------------------------------------------------------------%
% x/y/size/colour encoding preferences based on possible causal relationships in the data
% version 2 - alt - limited to quantitative encoding types

% for each pair of fields and pair of channels we have a preference of field to channel encoding,
% with the explanatory variable assigned to the higher priority channel
% the channel priority order is ['x', 'y', 'size', 'color']
% breaking these soft constraints incurs a cost of 100

% prefer x=region y=QoL_all
soft(rule_01_00_00,V) :- channel(V,E1,x), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,y), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_00_weight = 100.
soft_weight(rule_01_00_00,rule_01_00_00_weight).
% ----------------------------------------------------------------------------------------------------------------------%
% prefer x=region size=QoL_all
soft(rule_01_00_01,V) :- channel(V,E1,x), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,size), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_01_weight = 100.
soft_weight(rule_01_00_01,rule_01_00_01_weight).
% ----------------------------------------------------------------------------------------------------------------------%
% prefer x=region color=QoL_all
soft(rule_01_00_02,V) :- channel(V,E1,x), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,color), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_02_weight = 100.
soft_weight(rule_01_00_02,rule_01_00_02_weight).
% ----------------------------------------------------------------------------------------------------------------------%
% prefer y=region size=QoL_all
soft(rule_01_00_03,V) :- channel(V,E1,y), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,size), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_03_weight = 100.
soft_weight(rule_01_00_03,rule_01_00_03_weight).
% ----------------------------------------------------------------------------------------------------------------------%
% prefer y=region color=QoL_all
soft(rule_01_00_04,V) :- channel(V,E1,y), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,color), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_04_weight = 100.
soft_weight(rule_01_00_04,rule_01_00_04_weight).
% ----------------------------------------------------------------------------------------------------------------------%
% prefer size=region color=QoL_all
soft(rule_01_00_05,V) :- channel(V,E1,size), field(V,E1,"QoL_all"),
                         type(V,E1,quantitative),
                         channel(V,E2,color), field(V,E2,"region"),
                         type(V,E2,quantitative),
                         is_c_c(V).
#const rule_01_00_05_weight = 100.
soft_weight(rule_01_00_05,rule_01_00_05_weight).
% ----------------------------------------------------------------------------------------------------------------------%


% *** end of verde rule 01 lp *** --------------------------------------------------------------------------------------%
% --- verde rule 03 (sort order for ordinals) -------------------------------------------------------------------------%

% these facts state the association of a sort order to the field

fieldcustomsortorder("region","['England', 'North West', 'North East', 'Yorkshire and the Humber', 'West Midlands', 'East Midlands', 'South West', 'South East', 'Eastern', 'London']").


%----------------------------------------------------------------------------------------------------------------------%

% this rule determines that a custom order exists provided the
% resulting draco encoding is nominal or ordinal.

verde_ordinal_sort(V,E,C,F,O) :- fieldcustomsortorder(F,O),
                                 field(V,E,F), type(V,E,(nominal;ordinal)),
                                 channel(V,E,C).

%----------------------------------------------------------------------------------------------------------------------%

% outputs for translation to vl spec properties

#show verde_ordinal_sort/5.

% set this as zero weight soft rules, helps in the comparative analysis v baseline

soft(verde_ordinal_sort,V,E):- verde_ordinal_sort(V,E,C,F,O).
#const verde_ordinal_sort_weight = 0.
soft_weight(verde_ordinal_sort, verde_ordinal_sort_weight).

% *** end of verde rule 03 lp *** -------------------------------------------------------------------------------------%
% --- verde rule04 (colour schemes and mark colours) *** --------------------------------------------------------------%

% field to colour properties (facts)
fieldmarkcolor("region","{\"color\": \"#888888\"}",0).
fieldmarkcolor("region_code","{\"color\": \"#888888\"}",0).
fieldmarkcolor("zero_hr_contract_all_pct","{\"color\": \"#d18954\"}",1).
fieldmarkcolor("zero_hr_contract_managerial_pct","{\"color\": \"#d18954\"}",1).
fieldmarkcolor("zero_hr_contract_reg_prof_pct","{\"color\": \"#d18954\"}",1).
fieldmarkcolor("zero_hr_contract_direct_care_pct","{\"color\": \"#d18954\"}",1).
fieldmarkcolor("zero_hr_contract_other_pct","{\"color\": \"#d18954\"}",1).
fieldmarkcolor("vacancies_all_pct","{\"color\": \"#4da5a4\"}",2).
fieldmarkcolor("vacancies_managerial_pct","{\"color\": \"#4da5a4\"}",2).
fieldmarkcolor("vacancies_reg_prof_pct","{\"color\": \"#4da5a4\"}",2).
fieldmarkcolor("vacancies_direct_care_pct","{\"color\": \"#4da5a4\"}",2).
fieldmarkcolor("vacancies_other_pct","{\"color\": \"#4da5a4\"}",2).
fieldmarkcolor("QoL_all","{\"color\": \"#928ec3\"}",2).
fieldmarkcolor("QoL_male","{\"color\": \"#928ec3\"}",2).
fieldmarkcolor("QoL_female","{\"color\": \"#928ec3\"}",2).
fieldmarkcolor("QoL_18_64","{\"color\": \"#928ec3\"}",2).
fieldmarkcolor("QoL_65_over","{\"color\": \"#928ec3\"}",2).

fieldcolorscheme("region", "{\"scheme\": \"blues\"}",3).
fieldcolorscheme("region_code", "{\"scheme\": \"blues\"}",3).
fieldcolorscheme("zero_hr_contract_all_pct", "{\"scheme\": \"browns\"}",1).
fieldcolorscheme("zero_hr_contract_managerial_pct", "{\"scheme\": \"browns\"}",1).
fieldcolorscheme("zero_hr_contract_reg_prof_pct", "{\"scheme\": \"browns\"}",1).
fieldcolorscheme("zero_hr_contract_direct_care_pct", "{\"scheme\": \"browns\"}",1).
fieldcolorscheme("zero_hr_contract_other_pct", "{\"scheme\": \"browns\"}",1).
fieldcolorscheme("vacancies_all_pct", "{\"scheme\": \"teals\"}",2).
fieldcolorscheme("vacancies_managerial_pct", "{\"scheme\": \"teals\"}",2).
fieldcolorscheme("vacancies_reg_prof_pct", "{\"scheme\": \"teals\"}",2).
fieldcolorscheme("vacancies_direct_care_pct", "{\"scheme\": \"teals\"}",2).
fieldcolorscheme("vacancies_other_pct", "{\"scheme\": \"teals\"}",2).
fieldcolorscheme("QoL_all", "{\"scheme\": \"purples\"}",2).
fieldcolorscheme("QoL_male", "{\"scheme\": \"purples\"}",2).
fieldcolorscheme("QoL_female", "{\"scheme\": \"purples\"}",2).
fieldcolorscheme("QoL_18_64", "{\"scheme\": \"purples\"}",2).
fieldcolorscheme("QoL_65_over", "{\"scheme\": \"purples\"}",2).

% rule definitions

%----------------------------------------------------------------------------------------------------------------------%
% first case: color channel is used and we have a scheme for the encoding field.
verde_color_enc_scheme_choices(V,E,F,T,CS,D) :- fieldcolorscheme(F,CS,D), field(V,E,F), type(V,E,T), channel(V,E,color),
                                                D<3.

% choose only one with minimum distance from domain node with scheme to the mapped node
1 { verde_color_enc_scheme(V,E,F,T,CS,D) } 1 :- verde_color_enc_scheme_choices(V,E,F,T,CS,D),
                                                #min { DD : verde_color_enc_scheme_choices(_,_,_,_,_,DD) } = D.

%----------------------------------------------------------------------------------------------------------------------%
% second case: if first case not applied, and we have non-aggregated field encoding for which there is a schema,
% then we will double encode that field.
verde_color_double_enc_scheme_choices(V,E,F,T,CS,D) :- not channel(_,_,color),
                                                       not verde_color_enc_scheme(_,_,_,_,_,_),
                                                       field(V,E,F), type(V,E,T),
                                                       not aggregate(V,E,_),
                                                       discrete(V,E), fieldcolorscheme(F,CS,D),
                                                       D<2.
% choose only one
1 { verde_color_double_enc_scheme(V,E,F,T,CS,D) } 1 :- verde_color_double_enc_scheme_choices(V,E,F,T,CS,D),
                                                       #min { DD : verde_color_double_enc_scheme_choices(_,_,_,_,_,DD) }
                                                         = D.

%----------------------------------------------------------------------------------------------------------------------%
% third case: if first two cases does not apply but we have an appropriate mark color
verde_mark_color_choices(V,CO,D) :- not channel(_,_,color),
                                    not verde_color_enc_scheme(_,_,_,_,_,_),
                                    not verde_color_double_enc_scheme(_,_,_,_,_,_),
                                    view(V), fieldmarkcolor(F,CO,D),
                                    fieldtype(F,FT), FT != "number",
                                    cardinality(F,CA), num_rows(NR), CA = NR.

% choose only one mark colour with minimum distance between node with mark colour and mapped node
1 { verde_color_mark(V,CO,D) } 1 :- verde_mark_color_choices(V,CO,D),
                                    #min { DD : verde_mark_color_choices(_,_,DD) } = D.

%----------------------------------------------------------------------------------------------------------------------%

% outputs for translation to vl spec properties
#show verde_color_enc_scheme/6.
#show verde_color_double_enc_scheme/6.
#show verde_color_mark/3.

% set these as zero weight soft rules, helps in the comparative analysis v baseline
soft(verde_color_enc_scheme,V,E) :- verde_color_enc_scheme(V,E,F,T,CS,D).
soft(verde_color_double_enc_scheme,V,E) :- verde_color_double_enc_scheme(V,E,F,T,CS,D).
soft(verde_color_mark,V,CO) :- verde_color_mark(V,CO,D).

#const verde_color_enc_scheme_weight = 0.
#const verde_color_double_enc_scheme_weight = 0.
#const verde_color_mark_weight = 0.

soft_weight(verde_color_enc_scheme, verde_color_enc_scheme_weight).
soft_weight(verde_color_double_enc_scheme, verde_color_double_enc_scheme_weight).
soft_weight(verde_color_mark, verde_color_mark_weight).

% *** end of verde rule 04 lp *** -------------------------------------------------------------------------------------%
