view(v_v).
num_rows(63).

fieldtype("Region_code",string).
cardinality("Region_code", 9).
fieldtype("Region_name",string).
cardinality("Region_name", 9).
fieldtype("Setting",string).
cardinality("Setting", 7).
fieldtype("Gross_Current_Expenditure_x1000",number).
cardinality("Gross_Current_Expenditure_x1000", 63).
fieldtype("Gross_Current_Expenditure_Proportion",number).
cardinality("Gross_Current_Expenditure_Proportion", 63).

encoding(v_v,e0).
encoding(v_v,e1).
:- not field(v_v,E,"Setting") : encoding(v_v,E).
:- not field(v_v,E,"Gross_Current_Expenditure_x1000") : encoding(v_v,E).
:- field(v_v,E,"Gross_Current_Expenditure_x1000"), not zero(v_v,E).

% --- verde rule04 (colour schemes and mark colours) *** --------------------------------------------------------------%

% field to colour properties (facts)
fieldmarkcolor("Region_code","{\"color\": \"slategray\"}",1).
fieldmarkcolor("Region_name","{\"color\": \"black\"}",0).

fieldcolorscheme("Setting", "{\"scheme\": \"pastel1\"}",0).
fieldcolorscheme("Gross_Current_Expenditure_x1000", "{\"scheme\": \"oranges\"}",0).
fieldcolorscheme("Gross_Current_Expenditure_Proportion", "{\"scheme\": \"oranges\"}",0).

% rule definitions

%----------------------------------------------------------------------------------------------------------------------%
% first case: color channel is used and we have a scheme for the encoding field.
verde_color_enc_scheme_choices(V,E,F,T,CS,D) :- fieldcolorscheme(F,CS,D), field(V,E,F), type(V,E,T), channel(V,E,color).

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
                                                       discrete(V,E), fieldcolorscheme(F,CS,D).
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
