%*#include "../../../draco-fk/asp/define.lp".
#include "../../../draco-fk/asp/generate.lp".
#include "../../../draco-fk/asp/hard.lp".
#include "../../../draco-fk/asp/soft.lp".
#include "../../../draco-fk/asp/weights.lp".
#include "../../../draco-fk/asp/assign_weights.lp".
#include "../../../draco-fk/asp/optimize.lp".
#include "../../../draco-fk/asp/output.lp".*%

% ====== Definitions ======

% Types of marks to encode data.
marktype(point;bar;line;area;text;tick;rect).
% High level data types: quantitative, ordinal, nominal, temporal.
type(quantitative;ordinal;nominal;temporal).
% Basic types of the data.
primitive_type(string;number;boolean;datetime).
% Supported aggregation functions.
aggregate_op(count;mean;median;min;max;stdev;sum).
summative_aggregate_op(count;sum).
% Numbers of bins that can be recommended; any natural number is allowed.
binning(10;25).

% Encoding channels.
single_channel(x;y;color;size;shape;text;row;column).
multi_channel(detail).
channel(C) :- single_channel(C).
% channel(C) :- multi_channel(C).
non_positional(color;size;shape;text;detail).

% Possible tasks.
tasks(value;summary).

% Possible stackings.
stacking(zero;normalize).

% ====== Helpers ======

discrete(V,E) :- type(V,E,(nominal;ordinal)).
discrete(V,E) :- bin(V,E,_).
continuous(V,E) :- encoding(V,E), not discrete(V,E).

channel_discrete(V,C) :- discrete(V,E), channel(V,E,C).
channel_continuous(V,C) :- continuous(V,E), channel(V,E,C).

ordered(E) :- type(V,E,(ordinal;quantitative)).

% Fields
field(F) :- fieldtype(F,_).

% Stacking is applied to the continuous x or y.
stack(V,EC,S) :- channel(V,EC,(x;y)), channel(V,ED,(x;y)), continuous(V,EC), discrete(V,ED), stack(V,S).
% X and y are continuous.
stack(E,S) :- channel_continuous(V,x), channel(V,E,y), continuous(V,E), stack(V,S).

stack(V,S) :- encoding(V,E), stack(E,S).

% Data properties
enc_cardinality(V,E,C) :- field(V,E,F), cardinality(F,C).
enc_entropy(V,E,EN) :- field(V,E,F), entropy(F,EN).
enc_interesting(V,E) :- field(V,E,F), interesting(F).
enc_extent(V,E,MIN,MAX) :- field(V,E,F), extent(F,MIN,MAX).

% Cardinality of discrete field. A binned field has the cadinality of its field.
discrete_cardinality(V,E,CE) :- discrete(V,E), enc_cardinality(V,E,CE), channel(V,E,C), not bin(V,E,_).
discrete_cardinality(V,E,CB) :- channel(V,E,C), bin(V,E,CB).

% Define a fake soft/2 for all soft/1.
soft(F,V,_placeholder) :- soft(F,V).

% Silence warnings about properties never appearing in head.
entropy(0,0) :- #false.
interesting(0) :- #false.
extent(0,0,0) :- #false.
soft(0) :- #false.
task(0,value) :- #false.
task(0,summary) :- #false.
data(0) :- #false.
base(0) :- #false.

% == Chart Types ==

% Continuous by continuous.
is_c_c(V) :- channel_continuous(V,x), channel_continuous(V,y).

% Continuous by discrete (or continuous only).
is_c_d(V) :- channel_continuous(V,x), not channel_continuous(V,y).
is_c_d(V) :- channel_continuous(V,y), not channel_continuous(V,x).

% Discrete by discrete.
is_d_d(V) :- channel_discrete(V,x), channel_discrete(V,y).

% == Overlap ==

% The continuous variable is a measure (it is aggregated) and all other channels are .aggregated, or we use stack -> no overlap
non_pos_unaggregated(V) :- channel(V,E,C), non_positional(C), not aggregate(V,E,_).
no_overlap(V) :- is_c_d(V), continuous(V,E), channel(V,E,(x;y)), aggregate(V,E,_), not non_pos_unaggregated(V).
no_overlap(V) :- is_c_d(V), stack(V,_).

% the size of the discrete positional encoding
discrete_size(V,S) :- is_c_d(V), x_y_cardinality(V,_,S).
discrete_size(V,1) :- is_c_d(V), channel_continuous(V,x), not channel(V,_,y).
discrete_size(V,1) :- is_c_d(V), channel_continuous(V,y), not channel(V,_,x).

% Data size is as small as discrete dimension -> no overlap.
no_overlap(V) :- is_c_d(V), num_rows(S), discrete_size(V,S).

% We definitely overlap if the data size > discrete size.
overlap(V) :- is_c_d(V), not no_overlap(V), num_rows(S1), discrete_size(V,S2), S1 > S2.

% helpers to go from quadratic to linear number of grounding
x_y_cardinality(V,x,S) :- channel(V,E,x), discrete_cardinality(V,E,S).
x_y_cardinality(V,y,S) :- channel(V,E,y), discrete_cardinality(V,E,S).

% No overlap if all other dimensions are aggregated.
discrete_size(V,S) :- is_d_d(V), x_y_cardinality(V,x,SX), x_y_cardinality(V,y,SY), S = SX*SY.
no_overlap(V) :- is_d_d(V), not non_pos_unaggregated(V).
no_overlap(V) :- is_d_d(V), num_rows(S1), discrete_size(V,S2), S1 <= S2.  % This cannot guarantee no overlap.

% We can guarantee overlap using this rule unless we are using row / column.
row_col(V) :- channel(V,_,(row;column)).
overlap(V) :- is_d_d(V), channel(V,E,C), not row_col(V), not no_overlap(V), num_rows(S1), discrete_size(V,S2), S1 > S2.

% == Orientation ==

% Orientation tells us which one is the dependent and independent variable.

orientation(V,vertical) :- mark(V,(bar;tick;area;line)), channel_discrete(V,x).
orientation(V,vertical) :- mark(V,(area;line)), channel_continuous(V,x), channel_continuous(V,y).

orientation(V,horizontal) :- mark(V,(bar;tick;area;line)), channel_discrete(V,y).
% ====== Generators ======

% encodings

% maximum number for each multi channel encoding
#const max_extra_encs = 1.

obj_id(1..max_extra_encs).

{ encoding(V,E): obj_id(E) } :- view(V), not base(V).

:- not encoding(V,ID), not base(V), encoding(V,ID-1), obj_id(ID), obj_id(ID-1).

% don't add extra field
:- obj_id(ID), field(_,ID,_).

% properties of encodings

% channel and type have to be present
{ channel(V,E,C) : channel(C) } = 1 :- encoding(V,E), not base(V).
{ type(V,E,T): type(T) } = 1 :- encoding(V,E), not base(V).

% other properties that are not required
0 { field(V,E,F): field(F) } 1 :- encoding(V,E), not base(V).
0 { aggregate(V,E,A): aggregate_op(A) } 1 :- encoding(V,E), not base(V).
0 { bin(V,E,B): binning(B) } 1 :- encoding(V,E), not base(V).
0 { zero(V,E) } 1 :- encoding(V,E), not base(V).
0 { log(V,E) } 1 :- encoding(V,E), not base(V).

% pick one mark type

{ mark(V,M) : marktype(M) } = 1 :- view(V), not base(V).

% stacking

0 { stack(V,S): stacking(S) } 1 :- view(V), not base(V).

:- field(V,E1,F1), field(V,E2,F2), E1 > E2, F1 <= F2. %trubens
:- view(V), hard(_,V).
:- view(V), hard(_,V,_).
:- view(V), hard(_,V,_,_).

% ====== Expressiveness and Well-Formedness Constraints ======

% === Within Encodings ===

% @constraint Primitive type has to support data type.
hard(enc_type_valid,V,E,F) :- type(V,E,quantitative), field(V,E,F), fieldtype(F,(string;boolean)).
hard(enc_type_valid,V,E,F) :- type(V,E,temporal), field(V,E,F), not fieldtype(F,datetime).

% @constraint Can only bin quantitative or ordinal.
hard(bin_q_o,V,E,T) :- type(V,E,T), bin(V,E,_), T != quantitative, T != ordinal.

% @constraint Can only use log with quantitative.
hard(log_q,V,E) :- log(V,E), not type(V,E,quantitative).

% @constraint Can only use zero with quantitative.
hard(zero_q,V,E) :- zero(V,E), not type(V,E,quantitative).

% @constraint Cannot use log scale with discrete (which includes binned).
hard(log_discrete,V,E) :- log(V,E), discrete(V,E).

% @constraint Cannot use log and zero together.
hard(log_zero,V,E) :- log(V,E), zero(V,E).

% @constraint Cannot use log if the data is negative or zero.
hard(log_non_positive,V,E,F) :- log(V,E), field(V,E,F), extent(F,MIN,_), MIN <= 0.

% @constraint Cannot bin and aggregate.
hard(bin_and_aggregate,V,E) :- aggregate(V,E,_), bin(V,E,_).

% @constraint Oridnal only supports min, max, and median.
hard(aggregate_o_valid,V,E,A) :- aggregate(V,E,A), type(V,E,ordinal), A != min, A != max, A != median.

% @constraint Temporal only supports min and max.
hard(aggregate_t_valid,V,E,A) :- aggregate(V,E,A), type(V,E,temporal), A != min, A != max.

% @constraint Cannot aggregate nominal.
hard(aggregate_nominal,V,E) :- aggregate(V,E,_), type(V,E,nominal).

% @constraint Detail cannot be aggregated.
hard(aggregate_detail,V,E) :- channel(V,E,detail), aggregate(V,E,_).

% @constraint Count has to be quantitative and not use a field.
hard(count_q_without_field,V,E) :- aggregate(V,E,count), field(V,E,_).
hard(count_q_without_field,V,E) :- aggregate(V,E,count), not type(V,E,quantitative).

% @constraint Shape requires discrete and not ordered (nominal). Using ordinal would't make a difference in Vega-Lite.
hard(shape_discrete_non_ordered,V,E) :- channel(V,E,shape), not type(V,E,nominal).

% @constraint Detail requires nominal.
hard(detail_non_ordered,V,E) :- channel(V,E,detail), not type(V,E,nominal).

% @constraint Size implies order so nominal is misleading.
hard(size_nominal,V,E) :- channel(V,E,size), type(V,E,nominal).

% @constraint Do not use size when data is negative as size implies that data is positive.
hard(size_negative,V,E) :- channel(V,E,size), enc_extent(V,E,MIN,MAX), MIN < 0, MAX > 0.

% === Across encodings and between encodings and marks ===

% @constraint Cannot use single channels twice.
hard(repeat_channel,V,C) :- view(V), single_channel(C), 2 { channel(V,_,C) }.

% @constraint There has to be at least one encoding. Otherwise, the visualization doesn't show anything.
hard(no_encodings,V) :- view(V), not encoding(V,_).

% @constraint Row and column require discrete.
hard(row_or_column_c,V) :- channel_continuous(V,(row;column)).

% @constraint Don't use row without y. Just using y is simpler.
hard(row_no_y,V) :- channel(V,_,row), not channel(V,_,y).

% @constraint Don't use column without x. Just using x is simpler.
hard(column_no_x,V) :- channel(V,_,column), not channel(V,_,x).

% @constraint All encodings (if they have a channel) require field except if we have a count aggregate.
hard(encoding_no_field_and_not_count,V,E) :- not field(V,E,_), not aggregate(V,E,count), encoding(V,E).

% @constraint Count should not have a field. Having a field doesn't make a difference.
hard(count_with_field,V,E) :- aggregate(V,E,count), field(V,E,_).

% @constraint Text mark requires text channel.
hard(text_mark_without_text_channel,V) :- mark(V,text), not channel(V,_,text).

% @constraint Text channel requires text mark.
hard(text_channel_without_text_mark,V) :- channel(V,E,text), not mark(V,text).

% @constraint Point, tick, and bar require x or y channel.
hard(point_tick_bar_without_x_or_y,V) :- mark(V,(point;tick;bar)), not channel(V,_,x), not channel(V,_,y).

% @constraint Line and area require x and y channel.
hard(line_area_without_x_y,V) :- mark(V,(line;area)), not channel(V,_,(x;y)).

% @constraint Line and area cannot have two discrete.
hard(line_area_with_discrete,V) :- mark(V,(line;area)), channel_discrete(V,x), channel_discrete(V,y).

% @constraint Bar and tick cannot have both x and y continuous.
hard(bar_tick_continuous_x_y,V) :- mark(V,(bar;tick)), channel_continuous(V,x), channel_continuous(V,y).

% @constraint Bar, tick, line, area require some continuous variable on x or y.
hard(bar_tick_area_line_without_continuous_x_y,V) :- mark(V,(bar;tick;area;line)), not channel_continuous(V,x), not channel_continuous(V,y).

% @constraint Bar and area mark requires scale of continuous to start at zero.
hard(bar_area_without_zero,V) :- mark(V,(bar;area)), channel(V,E,x), orientation(V,horizontal), not zero(V,E).
hard(bar_area_without_zero,V) :- mark(V,(bar;area)), channel(V,E,y), orientation(V,vertical), not zero(V,E).

% @constraint Shape channel requires point mark.
hard(shape_without_point,V) :- channel(V,_,shape), not mark(V,point).

% @constraint Size only works with some marks. Vega-Lite can also size lines, and ticks but that would violate best practices.
hard(size_without_point_text,V) :-  channel(V,_,size), not mark(V,point), not mark(V,text).

% @constraint Detail requires aggregation. Detail adds a field to the group by. Detail could also be used to add information to tooltips. We may remove this later.
hard(detail_without_agg,V) :- channel(V,_,detail), not aggregate(V,_,_).

% @constraint Do not use log for bar or area mark as they are often misleading. We may remove this rule in the future.
hard(area_bar_with_log,V) :- mark(V,(bar;area)), channel(V,E,(x;y)), log(V,E).

% @constraint Rect mark needs discrete x and y.
hard(rect_without_d_d,V) :- mark(V,rect), not is_d_d(V).

% @constraint Don't use the same field on x and y.
hard(same_field_x_and_y,V) :- view(V), { field(V,E,F) : channel(V,E,x); field(V,E,F) : channel(V,E,y) } >= 2, field(F).

% @constraint Don't use count on x and y.
hard(count_on_x_and_y,V):- channel(V,EX,x), channel(V,EY,y), aggregate(V,EX,count), aggregate(V,EY,count).

% @constraint If we use aggregation, then all continuous fields need to be aggeragted.
hard(aggregate_not_all_continuous,V):- aggregate(V,E,_), continuous(V,E), not aggregate(V,E,_).

% @constraint Don't use count twice.
hard(count_twice) :- view(V), { aggregate(V,_,count) } = 2.

% === Global properties ===

% @constraint Bars and area cannot overlap.
hard(bar_area_overlap,V) :- mark(V,(bar;area)), overlap(V).

% @constraint Rects shouldn't overlap. They are used for dioscrete heatmaps.
hard(rect_overlap,V) :- mark(V,rect), overlap(V).

% == Stacking ==

% @constraint Only use stacking for bar and area.
hard(stack_without_bar_area,V) :- stack(V,_), not mark(V,bar), not mark(V,area).

% @constraint Don't stack if aggregation is not summative (summative are count, sum, distinct, valid, missing).
hard(stack_without_summative_agg,V,E,A) :- aggregate(V,E,A), stack(V,E,_), not summative_aggregate_op(A).

% @constraint Need to stack if we use bar, area with discrete color.
hard(no_stack_with_bar_area_discrete_color,V,E) :- mark(V,(bar;area)), encoding(V,E), channel(V,E,color), discrete(V,E), not stack(V,_).

% @constraint Can only use stack if we also use discrete color, or detail.
hard(stack_without_discrete_color_or_detail,V) :- stack(V,_), not channel_discrete(V,color), { channel(V,E,detail) } = 0.

% @constraint If we use stack and detail, we also have to use quantitative color.
hard(stack_detail_without_q_color,V) :- stack(V,_), channel(V,_,detail), not channel(V,_,color).
hard(stack_detail_without_q_color,V,E) :- stack(V,_), channel(V,_,detail), channel(V,E,color), not aggregate(V,E,_).

% @constraint Stack can only be on continuous.
hard(stack_discrete,V,E) :- encoding(V,E), stack(V,E,_), discrete(V,E).

% @constraint Stack can only be on x or y.
hard(stack_without_x_y,V,E) :- encoding(V,E), stack(V,E,_), not channel(V,E,x), not channel(V,E,y).

% @constraint Cannot use non positional continuous with stack unless it's aggregated.
hard(stack_with_non_positional_non_agg,V,E,C) :- stack(V,_), encoding(V,E), non_positional(C), channel(V,E,C), not aggregate(V,E,_), continuous(V,E).

% @constraint Vega-Lite currently supports 8 shapes.
hard(shape_with_cardinality_gt_eight,V,E,C) :- channel(V,E,shape), enc_cardinality(V,E,C), C > 8.

% @constraint At most 20 categorical colors.
hard(color_with_cardinality_gt_twenty,V,E,C) :- channel(V,E,color), discrete(V,E), enc_cardinality(V,E,C), C > 20.

% === Type checks ===

% @constraint Check mark.
hard(invalid_mark,V,M) :- mark(V,M), not marktype(M).

% @constraint Check types of encoding properties.
hard(invalid_channel,V,C) :- channel(V,_,C), not channel(C).
hard(invalid_field,V,F) :- field(V,_,F), not field(F).
hard(invalid_type,V,T) :- type(V,_,T), not type(T).
hard(invalid_agg,V,A) :- aggregate(V,_,A), not aggregate_op(A).
hard(invalid_bin,V,B) :- bin(V,_,B), not B >= 0.  % @constraint Bin has to be a natural number.

% @constraint Fieldtype has to be primitive type.
hard(invalid_fieldtype,V,T) :- view(V), fieldtype(_,T), not primitive_type(T).

% @constraint Task has to be one of the tasks.
hard(invalid_task,V,T) :- view(V), task(V,T), not tasks(T).

% @constraint Num_rows has to be larger than 0.
hard(invalid_num_rows,V,S) :- view(V), num_rows(S), S < 0.

% @constraint Cardinality has to be larger than 0.
hard(invalid_cardinality,V,C) :- view(V), cardinality(_,C), C < 0.

% @constraint Entropy has to be positive.
hard(invalid_entropy,V,E) :- view(V), entropy(_,E), E < 0.

% @constraint Extent only allowed for numbers (for now).
hard(invalid_extent_non_number,V,F) :- view(V), extent(F,_,_), not fieldtype(F,number).

% @constraint Order has to be correct.
hard(invalid_extent_order,V,MIN,MAX):- view(V), extent(_,MIN,MAX), MIN > MAX.

% @constraint The name of a field cannot be the name of an encoding. This is to prevent errors coming from the shortcuts in define.lp.
hard(encoding_field_same_name,V,N) :- view(V), encoding(V,N), field(N).

% @constraint Cannot bin strings.
hard(bin_string,V,E) :- field(V,E,F), fieldtype(F,string), bin(V,E,_).
% After adding a soft constraint to this file, make sure to update `weights.lp` and run `process_softs.py`..

% ====== Preferences ======

% @constraint Prefer to use raw (no aggregate).
soft(aggregate,V,E) :- aggregate(V,E,_).

% @constraint Prefer to not bin.
soft(bin,V,E) :- bin(V,E,_).

% @constraint Prefer binning with at most 12 buckets.
soft(bin_high,V,E) :- bin(V,E,B), B > 12.

% @constraint Prefer binning with more than 7 buckets.
soft(bin_low,V,E) :- bin(V,E,B), B <= 7.

% @constraint Prefer to use fewer encodings.
soft(encoding,V,E) :- encoding(V,E).

% @constraint Prefer to use fewer encodings with fields (count does not have a field).
soft(encoding_field,V,E) :- field(V,E,_).

% @constraint Prefer not to use the same field twice.
soft(same_field_2,V,F) :- view(V), field(F), { field(V,_,F) } = 2.

% @constraint Prefer not to use the same field three or more times.
soft(same_field_gte3,V,F) :- view(V), field(F), { field(V,_,F) } >= 3.

% @constraint Prefer not to use count more than once.
soft(count_twice,V) :- view(V), { aggregate(V,_,count) } = 2.

% @constraint Shape channel should not have too high cardinality.
soft(shape_cardinality,V,E) :- channel(V,E,shape), discrete_cardinality(V,E,C), C > 5.

% @constraint Prefer nominal string fields
soft(string_non_nominal,V,E) :- type(V,E,ordinal), field(V,E,F), fieldtype(F,string).
soft(string_non_nominal,V,E) :- type(V,E,temporal), field(V,E,F), fieldtype(F,string).
soft(string_non_nominal,V,E) :- type(V,E,quantitative), field(V,E,F), fieldtype(F,string).

% @constraint Numbers should not be nominal.
soft(number_nominal,V,E) :- type(V,E,nominal), field(V,E,F), fieldtype(F,number).

% @constraint Numbers should not be ordinal with high cardinality.
soft(number_high_cardinality_ordinal,V,E) :- type(V,E,ordinal), field(V,E,F), fieldtype(F,number), enc_cardinality(V,E,C), C > 20.

% @constraint Binned quantitative field should not have too low cardinality.
soft(bin_cardinality,V,E) :- type(V,E,quantitative), bin(V,E,_), enc_cardinality(V,E,C), C < 15.

% @constraint Prefer quantitative for bin.
soft(quant_bin,V,E) :- bin(V,E,_), not type(V,E,quantitative).

% @constraint Plots with only nominal, ordinal, binned q, or t with time unit should add either an aggregation (e.g. count) or a quantitative field.
soft(only_discrete,V) :- view(V), not continuous(V,_).

% @constraint Prefer not to use multiple non-positional encoding channels.
soft(multiple_non_pos,V) :- view(V), { channel(V,_,C): non_positional(C) } > 1.

% @constraint Prefer not to use non-positional channels until all positional channels are used.
soft(non_positional_pref,V) :- channel(V,_,C), non_positional(C), not channel(V,_,(x;y)).

% @constraint Aggregate plots should not use raw continuous as group by.
soft(aggregate_group_by_raw,E) :- aggregate(V,_,_), continuous(V,E), not aggregate(V,E,_).

% @constraint Aggregate should also have a discrete encoding to group by.
soft(agg_dim,V) :- aggregate(V,_,_), not discrete(V,_).

% @constraint Prefer not to use plot with both x and y discrete and no aggregate as it leads to occlusion.
soft(x_y_raw,V,E) :- channel(V,EX,x), discrete(V,EX), channel(V,EY,y), discrete(V,EY), encoding(V,E), not aggregate(V,E,_), continuous(V,E).

% @constraint Prefer not to use log scale.
soft(log,V,E) :- log(V,E).

% @constraint Prefer to include zero for continuous (binned doesn't need zero).
soft(zero,V,E) :- continuous(V,E), not zero(V,E).

% @constraint Prefer to exclude zero for binned.
soft(zero_bin,V,E) :- bin(V,E,_), zero(V,E).

% @constraint Prefer zero size (even when binned).
soft(zero_size,V) :- channel(V,E,size), not zero(V,E).

% @constraint Prefer zero positional.
soft(zero_positional,V) :- continuous(V,E), channel(V,E,(x;y)), not zero(V,E).

% @constraint Prefer not to use zero when the difference between min and max is larger than distance to 0.
soft(zero_skew,V) :- enc_extent(V,E,MIN,MAX), EX = MAX - MIN, |MAX| > EX, |MIN| > EX, zero(V,E).

% @constraint Do not include zero when the range of data includes zero.
soft(includes_zero,V,E) :- zero(V,E), field(V,E,F), extent(F,MIN,MAX), MIN < 0, MAX > 0.

% @constraint Prefer to use only x instead of only y.
soft(only_x,V) :- channel(V,_,y), not channel(V,_,x).

% @constraint Chart orientation for bar and tick (with and without bin). Binned fields have short labels if they are quantitative while otherwise labels can be long.
soft(orientation_binned,V) :- mark(V,(bar;tick)), bin(V,E,_), type(V,E,quantitative), not channel(V,E,x).

% @constraint Prefer not to use ordinal for fields with high cardinality.
soft(high_cardinality_ordinal,V,E) :- type(V,E,ordinal), discrete_cardinality(V,E,C), C > 30.

% @constraint Prefer not to use nominal for fields with high cardinality.
soft(high_cardinality_nominal,V,E) :- type(V,E,nominal), enc_cardinality(V,E,C), C > 12.

% @constraint Prefer not to use high cardinality nominal for color.
soft(high_cardinality_nominal_color,V,E) :- type(V,E,nominal), channel(V,E,color), enc_cardinality(V,E,C), C > 10.

% @constraint Avoid high cardinality on x or column as it causes horizontal scrolling.
soft(horizontal_scrolling,V,E) :- channel(V,E,x), discrete_cardinality(V,E,C), C > 50.
soft(horizontal_scrolling,V,E) :- channel(V,E,columm), discrete_cardinality(V,E,C), C > 5.

% @constraint Prefer to use temporal type with dates.
soft(temporal_date,V,E) :- field(V,E,F), fieldtype(F,datetime), not type(V,E,temporal).

% @constraint Prefer quantitative for numbers with high cardinality.
soft(quantitative_numbers,V) :- field(V,E,F), fieldtype(F,number), cardinality(F,C), C > 20, not bin(V,E,_), not type(V,E,quantitative).

% @constraint Overplotting. Prefer not to use x and y for continuous with high cardinality and low entropy without aggregation because the points will overplot.
soft(position_entropy,V,E) :- channel(V,E,(x;y)), continuous(V,E), enc_cardinality(V,E,C), C > 100, enc_entropy(V,E,EN), EN <= 12, not aggregate(V,E,_).

% @constraint Prefer not to use size when the cardinality is large on x or y.
soft(high_cardinality_size,V,E) :- continuous(V,E), channel(V,_,size), enc_cardinality(V,E,C), C > 100, channel(V,E,(x;y)).

% @constraint Prefer not to aggregate for value tasks.
soft(value_agg,V) :- task(V,value), aggregate(V,_,_).

% @constraint Prefer not to use row and column for summary tasks as it makes it difficult to compare.
soft(facet_summary,V,E) :- task(V,summary), channel(V,E,row).

% @constraint Positional interactions as suggested by Kim et al.
soft(x_row,V) :- channel(V,_,x), channel(V,_,row).

% @constraint Positional interactions as suggested by Kim et al.
soft(y_row,V) :- channel(V,_,y), channel(V,_,row).

% @constraint Positional interactions as suggested by Kim et al.
soft(x_column,V) :- channel(V,_,x), channel(V,_,column).

% @constraint Positional interactions as suggested by Kim et al.
soft(y_column,V) :- channel(V,_,y), channel(V,_,column).

% @constraint Entropy, primary quantitaty interactions as suggested by Kim et al.
soft(color_entropy_high,V,E) :- channel(V,E,color), enc_entropy(V,E,EN), EN > 12, type(V,E,quantitative), enc_interesting(V,E).

% @constraint Entropy, primary quantitaty interactions as suggested by Kim et al.
soft(color_entropy_low,V,E) :- channel(V,E,color), enc_entropy(V,E,EN), EN <= 12, type(V,E,quantitative), enc_interesting(V,E).

% @constraint Entropy, primary quantitaty interactions as suggested by Kim et al.
soft(size_entropy_high,V,E) :- channel(V,E,size), enc_entropy(V,E,EN), EN > 12, type(V,E,quantitative), enc_interesting(V,E).

% @constraint Entropy, primary quantitaty interactions as suggested by Kim et al.
soft(size_entropy_low,V,E) :- channel(V,E,size), enc_entropy(V,E,EN), EN <= 12, type(V,E,quantitative), enc_interesting(V,E).

% @constraint Prefer not to use continuous on x, discrete on y, and column.
soft(c_d_column,V) :- channel_continuous(V,x), channel_discrete(V,y), channel(V,_,column).

% @constraint Prefer time on x.
soft(temporal_y,V) :- type(V,E,temporal), not channel(V,E,x).

% @constraint Prefer not to overlap with DxD.
soft(d_d_overlap,V) :- is_d_d(V), overlap(V).

% ====== Rankings ======
% === Data Types ===

% @constraint Prefer quantitative > ordinal > nominal.
soft(type_q,V,E) :- type(V,E,quantitative).

% @constraint Prefer quantitative > ordinal > nominal.
soft(type_o,V,E) :- type(V,E,ordinal).

% @constraint Prefer quantitative > ordinal > nominal.
soft(type_n,V,E) :- type(V,E,nominal).

% === Mark types ===

% @constraint Continuous by continuous for point mark.
soft(c_c_point,V) :- is_c_c(V), mark(V,point).

% @constraint Continuous by continuous for line mark.
soft(c_c_line,V) :- is_c_c(V), mark(V,line).

% @constraint Continuous by continuous for area mark.
soft(c_c_area,V) :- is_c_c(V), mark(V,area).

% @constraint Continuous by continuous for text mark.
soft(c_c_text,V) :- is_c_c(V), mark(V,text).

% @constraint Continuous by continuous for tick mark.
soft(c_c_tick,V) :- is_c_c(V), mark(V,tick).

% @constraint Continuous by discrete for point mark.
soft(c_d_point,V) :- is_c_d(V), not no_overlap(V), mark(V,point).

% @constraint Continuous by discrete for bar mark.
soft(c_d_bar,V) :- is_c_d(V), not no_overlap(V), mark(V,bar).

% @constraint Continuous by discrete for line mark.
soft(c_d_line,V) :- is_c_d(V), not no_overlap(V), mark(V,line).

% @constraint Continuous by discrete for area mark.
soft(c_d_area,V) :- is_c_d(V), not no_overlap(V), mark(V,area).

% @constraint Continuous by discrete for text mark.
soft(c_d_text,V) :- is_c_d(V), not no_overlap(V), mark(V,text).

% @constraint Continuous by discrete for tick mark.
soft(c_d_tick,V) :- is_c_d(V), not no_overlap(V), mark(V,tick).

% @constraint Continuous by discrete for point mark with no overlap.
soft(c_d_no_overlap_point,V) :- is_c_d(V), no_overlap(V), mark(V,point).

% @constraint Continuous by discrete for bar mark with no overlap.
soft(c_d_no_overlap_bar,V) :- is_c_d(V), no_overlap(V), mark(V,bar).

% @constraint Continuous by discrete for line mark with no overlap.
soft(c_d_no_overlap_line,V) :- is_c_d(V), no_overlap(V), mark(V,line).

% @constraint Continuous by discrete for area mark with no overlap.
soft(c_d_no_overlap_area,V) :- is_c_d(V), no_overlap(V), mark(V,area).

% @constraint Continuous by discrete for text mark with no overlap.
soft(c_d_no_overlap_text,V) :- is_c_d(V), no_overlap(V), mark(V,text).

% @constraint Continuous by discrete for tick mark with no overlap.
soft(c_d_no_overlap_tick,V) :- is_c_d(V), no_overlap(V), mark(V,tick).

% @constraint Discrete by discrete for point mark.
soft(d_d_point,V) :- is_d_d(V), mark(V,point).

% @constraint Discrete by discrete for point mark.
soft(d_d_text,V) :- is_d_d(V), mark(V,text).

% @constraint Discrete by discrete for point mark.
soft(d_d_rect,V) :- is_d_d(V), mark(V,rect).

% === Channel rankings à la APT ===

% @constraint Continuous on x channel.
soft(continuous_x,V,E) :- channel(V,E,x), continuous(V,E).

% @constraint Continuous on y channel.
soft(continuous_y,V,E) :- channel(V,E,y), continuous(V,E).

% @constraint Continuous on color channel.
soft(continuous_color,V,E) :- channel(V,E,color), continuous(V,E).

% @constraint Continuous on size channel.
soft(continuous_size,V,E) :- channel(V,E,size), continuous(V,E).

% @constraint Continuous on text channel.
soft(continuous_text,V,E) :- channel(V,E,text), continuous(V,E).

% @constraint Ordered on x channel.
soft(ordered_x,V,E) :- channel(V,E,x), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on y channel.
soft(ordered_y,V,E) :- channel(V,E,y), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on color channel.
soft(ordered_color,V,E) :- channel(V,E,color), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on size channel.
soft(ordered_size,V,E) :- channel(V,E,size), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on text channel.
soft(ordered_text,V,E) :- channel(V,E,text), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on row channel.
soft(ordered_row,V,E) :- channel(V,E,row), discrete(V,E), not type(V,E,nominal).

% @constraint Ordered on column channel.
soft(ordered_column,V,E) :- channel(V,E,column), discrete(V,E), not type(V,E,nominal).

% @constraint Nominal on x channel.
soft(nominal_x,V,E) :- channel(V,E,x), type(V,E,nominal).

% @constraint Nominal on y channel.
soft(nominal_y,V,E) :- channel(V,E,y), type(V,E,nominal).

% @constraint Nominal on color channel.
soft(nominal_color,V,E) :- channel(V,E,color), type(V,E,nominal).

% @constraint Nominal on shape channel.
soft(nominal_shape,V,E) :- channel(V,E,shape), type(V,E,nominal).

% @constraint Nominal on text channel.
soft(nominal_text,V,E) :- channel(V,E,text), type(V,E,nominal).

% @constraint Nominal on row channel.
soft(nominal_row,V,E) :- channel(V,E,row), type(V,E,nominal).

% @constraint Nominal on column channel.
soft(nominal_column,V,E) :- channel(V,E,column), type(V,E,nominal).

% @constraint Nominal on detail channel.
soft(nominal_detail,V,E) :- channel(V,E,detail), type(V,E,nominal).

% @constraint Interesting on x channel.
soft(interesting_x,V,E) :- channel(V,E,x), enc_interesting(V,E).

% @constraint Interesting on y channel.
soft(interesting_y,V,E) :- channel(V,E,y), enc_interesting(V,E).

% @constraint Interesting on color channel.
soft(interesting_color,V,E) :- channel(V,E,color), enc_interesting(V,E).

% @constraint Interesting on size channel.
soft(interesting_size,V,E) :- channel(V,E,size), enc_interesting(V,E).

% @constraint Interesting on shape channel.
soft(interesting_shape,V,E) :- channel(V,E,shape), enc_interesting(V,E).

% @constraint Interesting on text channel.
soft(interesting_text,V,E) :- channel(V,E,text), enc_interesting(V,E).

% @constraint Interesting on row channel.
soft(interesting_row,V,E) :- channel(V,E,row), enc_interesting(V,E).

% @constraint Interesting on column channel.
soft(interesting_column,V,E) :- channel(V,E,column), enc_interesting(V,E).

% @constraint Interesting on detail channel.
soft(interesting_detail,V,E) :- channel(V,E,detail), enc_interesting(V,E).

% === Aggregations ===

% @constraint Count as aggregate op.
soft(aggregate_count,V,E) :- aggregate(V,E,count).

% @constraint Sum as aggregate op.
soft(aggregate_sum,V,E) :- aggregate(V,E,sum).

% @constraint Mean as aggregate op.
soft(aggregate_mean,V,E) :- aggregate(V,E,mean).

% @constraint Median as aggregate op.
soft(aggregate_median,V,E) :- aggregate(V,E,median).

% @constraint Min as aggregate op.
soft(aggregate_min,V,E) :- aggregate(V,E,min).

% @constraint Max as aggregate op.
soft(aggregate_max,V,E) :- aggregate(V,E,max).

% @constraint Standard Deviation as aggregate op.
soft(aggregate_stdev,V,E) :- aggregate(V,E,stdev).

% === Stack ===

% @constraint Zero base for stack op.
soft(stack_zero,V) :- stack(V,zero).

% @constraint Normalize between groupbys as stack op.
soft(stack_normalize,V) :- stack(V,normalize).

% === Task - marktype correlations ===

% @constraint Point mark for value tasks.
soft(value_point,V) :- task(V,value), mark(V,point).

% @constraint Bar mark for value tasks.
soft(value_bar,V) :- task(V,value), mark(V,bar).

% @constraint Line mark for value tasks.
soft(value_line,V) :- task(V,value), mark(V,line).

% @constraint Area mark for value tasks.
soft(value_area,V) :- task(V,value), mark(V,area).

% @constraint Text mark for value tasks.
soft(value_text,V) :- task(V,value), mark(V,text).

% @constraint Tick mark for value tasks.
soft(value_tick,V) :- task(V,value), mark(V,tick).
% @end

% @constraint Rect mark for value tasks.
soft(value_rect,V) :- task(V,value), mark(V,rect).

% @constraint Point mark for summary tasks.
soft(summary_point,V) :- task(V,summary), mark(V,point).

% @constraint Bar mark for summary tasks.
soft(summary_bar,V) :- task(V,summary), mark(V,bar).

% @constraint Line mark for summary tasks.
soft(summary_line,V) :- task(V,summary), mark(V,line).

% @constraint Area mark for summary tasks.
soft(summary_area,V) :- task(V,summary), mark(V,area).

% @constraint Text mark for summary tasks.
soft(summary_text,V) :- task(V,summary), mark(V,text).

% @constraint Tick mark for summary tasks.
soft(summary_tick,V) :- task(V,summary), mark(V,tick).

% @constraint Rect mark for summary tasks.
soft(summary_rect,V) :- task(V,summary), mark(V,rect).

% === Task - channel correlations ===

% @constraint Continuous x for value tasks.
soft(value_continuous_x,V,E) :- task(V,value), channel(V,E,x), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous y for value tasks.
soft(value_continuous_y,V,E) :- task(V,value), channel(V,E,y), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous color for value tasks.
soft(value_continuous_color,V,E) :- task(V,value), channel(V,E,color), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous size for value tasks.
soft(value_continuous_size,V,E) :- task(V,value), channel(V,E,size), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous text for value tasks.
soft(value_continuous_text,V,E) :- task(V,value), channel(V,E,text), continuous(V,E), enc_interesting(V,E).

% @constraint Discrete x for value tasks.
soft(value_discrete_x,V,E) :- task(V,value), channel(V,E,x), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete y for value tasks.
soft(value_discrete_y,V,E) :- task(V,value), channel(V,E,y), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete color for value tasks.
soft(value_discrete_color,V,E) :- task(V,value), channel(V,E,color), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete shape for value tasks.
soft(value_discrete_shape,V,E) :- task(V,value), channel(V,E,shape), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete size for value tasks.
soft(value_discrete_size,V,E) :- task(V,value), channel(V,E,size), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete text for value tasks.
soft(value_discrete_text,V,E) :- task(V,value), channel(V,E,text), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete row for value tasks.
soft(value_discrete_row,V,E) :- task(V,value), channel(V,E,row), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete column for value tasks.
soft(value_discrete_column,E) :- task(V,value), channel(V,E,column), discrete(V,E), enc_interesting(V,E).

% @constraint Continuous x for summary tasks.
soft(summary_continuous_x,E) :- task(V,summary), channel(V,E,x), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous y for summary tasks.
soft(summary_continuous_y,E) :- task(V,summary), channel(V,E,y), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous color for summary tasks.
soft(summary_continuous_color,E) :- task(V,summary), channel(V,E,color), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous size for summary tasks.
soft(summary_continuous_size,E) :- task(V,summary), channel(V,E,size), continuous(V,E), enc_interesting(V,E).

% @constraint Continuous text for summary tasks.
soft(summary_continuous_text,E) :- task(V,summary), channel(V,E,text), continuous(V,E), enc_interesting(V,E).

% @constraint Discrete x for summary tasks.
soft(summary_discrete_x,E) :- task(V,summary), channel(V,E,x), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete y for summary tasks.
soft(summary_discrete_y,E) :- task(V,summary), channel(V,E,y), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete color for summary tasks.
soft(summary_discrete_color,E) :- task(V,summary), channel(V,E,color), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete shape for summary tasks.
soft(summary_discrete_shape,E) :- task(V,summary), channel(V,E,shape), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete size for summary tasks.
soft(summary_discrete_size,E) :- task(V,summary), channel(V,E,size), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete text for summary tasks.
soft(summary_discrete_text,E) :- task(V,summary), channel(V,E,text), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete row for summary tasks.
soft(summary_discrete_row,E) :- task(V,summary), channel(V,E,row), discrete(V,E), enc_interesting(V,E).

% @constraint Discrete column for summary tasks.
soft(summary_discrete_column,E) :- task(V,summary), channel(V,E,column), discrete(V,E), enc_interesting(V,E).

% @constraint Tiebreaker to keep fields on x and y consistent.
soft(x_y_fields_order,V) :- field(V,EX,F1), field(V,EY,F2), channel(V,EX,x), channel(V,EY,y), F1 > F2. %trubens

% @constraint Rect without aggregate
% soft(d_d_rect_point_no_agg,V,none) :- mark(V,(point;rect)), is_d_d(V), not aggregate(V,_,_).
% Weights as constants



#const type_q_weight = 0.
#const type_o_weight = 1.
#const type_n_weight = 2.
#const aggregate_weight = 4.
#const bin_weight = 2.
#const bin_high_weight = 10.
#const bin_low_weight = 6.
#const encoding_weight = 0.
#const encoding_field_weight = 6.
#const same_field_2_weight = 8.
#const same_field_gte3_weight = 16.
#const count_twice_weight = 50.
#const shape_cardinality_weight = 5.
#const string_non_nominal_weight = 100.
#const number_nominal_weight = 50.
#const number_high_cardinality_ordinal_weight = 50.
#const bin_cardinality_weight = 5.
#const quant_bin_weight = 1.
#const agg_dim_weight = 2.
#const only_discrete_weight = 30.
#const multiple_non_pos_weight = 3.
#const non_positional_pref_weight = 40.
#const aggregate_group_by_raw_weight = 20.
#const x_y_raw_weight = 1.
#const log_weight = 1.
#const zero_weight = 1.
#const zero_bin_weight = 1.
#const zero_size_weight = 3.
#const zero_positional_weight = 1.
#const zero_skew_weight = 5.
#const includes_zero_weight = 10.

#const only_x_weight = 1.
#const orientation_binned_weight = 2.
#const high_cardinality_ordinal_weight = 10.
#const high_cardinality_nominal_weight = 10.
#const high_cardinality_nominal_color_weight = 10.
#const horizontal_scrolling_weight = 20.
#const temporal_date_weight = 1.
#const quantitative_numbers_weight = 2.
#const position_entropy_weight = 2.
#const high_cardinality_size_weight = 1.
#const value_agg_weight = 1.
#const facet_summary_weight = 0.
#const x_row_weight = 1.
#const y_row_weight = 1.
#const x_column_weight = 1.
#const y_column_weight = 1.
#const color_entropy_high_weight = 0.
#const color_entropy_low_weight = 0.
#const size_entropy_high_weight = 0.
#const size_entropy_low_weight = 0.

#const c_d_column_weight = 5.
#const temporal_y_weight = 1.
#const d_d_overlap_weight = 20.

#const c_c_point_weight = 0.
#const c_c_line_weight = 20.
#const c_c_area_weight = 20.
#const c_c_text_weight = 2.
#const c_c_tick_weight = 5.

#const c_d_point_weight = 10.
#const c_d_bar_weight = 20.
#const c_d_line_weight = 20.
#const c_d_area_weight = 20.
#const c_d_text_weight = 50.
#const c_d_tick_weight = 0.

#const c_d_no_overlap_point_weight = 10.
#const c_d_no_overlap_bar_weight = 0.
#const c_d_no_overlap_line_weight = 20.
#const c_d_no_overlap_area_weight = 20.
#const c_d_no_overlap_text_weight = 30.
#const c_d_no_overlap_tick_weight = 25.

#const d_d_point_weight = 0.
#const d_d_text_weight = 1.
#const d_d_rect_weight = 0.

#const continuous_x_weight = 0.
#const continuous_y_weight = 0.
#const continuous_color_weight = 10.
#const continuous_size_weight = 1.
#const continuous_text_weight = 20.

#const ordered_x_weight = 1.
#const ordered_y_weight = 0.
#const ordered_color_weight = 8.
#const ordered_size_weight = 10.
#const ordered_text_weight = 32.
#const ordered_row_weight = 10.
#const ordered_column_weight = 10.

#const nominal_x_weight = 3.
#const nominal_y_weight = 0.
#const nominal_color_weight = 6.
#const nominal_shape_weight = 10.
#const nominal_text_weight = 15.
#const nominal_row_weight = 8.
#const nominal_column_weight = 9.
#const nominal_detail_weight = 30.

#const interesting_x_weight = 0.
#const interesting_y_weight = 1.
#const interesting_color_weight = 2.
#const interesting_size_weight = 2.
#const interesting_shape_weight = 3.
#const interesting_text_weight = 6.
#const interesting_row_weight = 6.
#const interesting_column_weight = 7.
#const interesting_detail_weight = 20.

#const aggregate_count_weight = 0.
#const aggregate_sum_weight = 2.
#const aggregate_mean_weight = 1.
#const aggregate_median_weight = 3.
#const aggregate_min_weight = 4.
#const aggregate_max_weight = 4.
#const aggregate_stdev_weight = 5.

#const value_point_weight = 0.
#const value_bar_weight = 0.
#const value_line_weight = 0.
#const value_area_weight = 0.
#const value_text_weight = 0.
#const value_tick_weight = 0.
#const value_rect_weight = 0.
#const summary_point_weight = 0.
#const summary_bar_weight = 0.
#const summary_line_weight = 0.
#const summary_area_weight = 0.
#const summary_text_weight = 0.
#const summary_tick_weight = 0.
#const summary_rect_weight = 0.

#const value_continuous_x_weight = 0.
#const value_continuous_y_weight = 0.
#const value_continuous_color_weight = 0.
#const value_continuous_size_weight = 0.
#const value_continuous_text_weight = 0.
#const value_discrete_x_weight = 0.
#const value_discrete_y_weight = 0.
#const value_discrete_color_weight = 0.
#const value_discrete_shape_weight = 0.
#const value_discrete_size_weight = 0.
#const value_discrete_text_weight = 0.
#const value_discrete_row_weight = 0.
#const value_discrete_column_weight = 0.
#const summary_continuous_x_weight = 0.
#const summary_continuous_y_weight = 0.
#const summary_continuous_color_weight = 0.
#const summary_continuous_size_weight = 0.
#const summary_continuous_text_weight = 0.
#const summary_discrete_x_weight = 0.
#const summary_discrete_y_weight = 0.
#const summary_discrete_color_weight = 0.
#const summary_discrete_shape_weight = 0.
#const summary_discrete_size_weight = 0.
#const summary_discrete_text_weight = 0.
#const summary_discrete_row_weight = 0.
#const summary_discrete_column_weight = 0.

#const stack_zero_weight = 0.
#const stack_normalize_weight = 1.
#const x_y_fields_order_weight = 1.
#const rect_no_agg_weight = 40.
%% GENERATED FILE. DO NOT EDIT.

soft_weight(type_q,type_q_weight).
soft_weight(type_o,type_o_weight).
soft_weight(type_n,type_n_weight).
soft_weight(aggregate,aggregate_weight).
soft_weight(bin,bin_weight).
soft_weight(bin_high,bin_high_weight).
soft_weight(bin_low,bin_low_weight).
soft_weight(encoding,encoding_weight).
soft_weight(encoding_field,encoding_field_weight).
soft_weight(same_field_2,same_field_2_weight).
soft_weight(same_field_gte3,same_field_gte3_weight).
soft_weight(count_twice,count_twice_weight).
soft_weight(shape_cardinality,shape_cardinality_weight).
soft_weight(string_non_nominal,string_non_nominal_weight).
soft_weight(number_nominal,number_nominal_weight).
soft_weight(number_high_cardinality_ordinal,number_high_cardinality_ordinal_weight).
soft_weight(bin_cardinality,bin_cardinality_weight).
soft_weight(quant_bin,quant_bin_weight).
soft_weight(agg_dim,agg_dim_weight).
soft_weight(only_discrete,only_discrete_weight).
soft_weight(multiple_non_pos,multiple_non_pos_weight).
soft_weight(non_positional_pref,non_positional_pref_weight).
soft_weight(aggregate_group_by_raw,aggregate_group_by_raw_weight).
soft_weight(x_y_raw,x_y_raw_weight).
soft_weight(log,log_weight).
soft_weight(zero,zero_weight).
soft_weight(zero_bin,zero_bin_weight).
soft_weight(zero_size,zero_size_weight).
soft_weight(zero_positional,zero_positional_weight).
soft_weight(zero_skew,zero_skew_weight).
soft_weight(includes_zero,includes_zero_weight).
soft_weight(only_x,only_x_weight).
soft_weight(orientation_binned,orientation_binned_weight).
soft_weight(high_cardinality_ordinal,high_cardinality_ordinal_weight).
soft_weight(high_cardinality_nominal,high_cardinality_nominal_weight).
soft_weight(high_cardinality_nominal_color,high_cardinality_nominal_color_weight).
soft_weight(horizontal_scrolling,horizontal_scrolling_weight).
soft_weight(temporal_date,temporal_date_weight).
soft_weight(quantitative_numbers,quantitative_numbers_weight).
soft_weight(position_entropy,position_entropy_weight).
soft_weight(high_cardinality_size,high_cardinality_size_weight).
soft_weight(value_agg,value_agg_weight).
soft_weight(facet_summary,facet_summary_weight).
soft_weight(x_row,x_row_weight).
soft_weight(y_row,y_row_weight).
soft_weight(x_column,x_column_weight).
soft_weight(y_column,y_column_weight).
soft_weight(color_entropy_high,color_entropy_high_weight).
soft_weight(color_entropy_low,color_entropy_low_weight).
soft_weight(size_entropy_high,size_entropy_high_weight).
soft_weight(size_entropy_low,size_entropy_low_weight).
soft_weight(c_d_column,c_d_column_weight).
soft_weight(temporal_y,temporal_y_weight).
soft_weight(d_d_overlap,d_d_overlap_weight).
soft_weight(c_c_point,c_c_point_weight).
soft_weight(c_c_line,c_c_line_weight).
soft_weight(c_c_area,c_c_area_weight).
soft_weight(c_c_text,c_c_text_weight).
soft_weight(c_c_tick,c_c_tick_weight).
soft_weight(c_d_point,c_d_point_weight).
soft_weight(c_d_bar,c_d_bar_weight).
soft_weight(c_d_line,c_d_line_weight).
soft_weight(c_d_area,c_d_area_weight).
soft_weight(c_d_text,c_d_text_weight).
soft_weight(c_d_tick,c_d_tick_weight).
soft_weight(c_d_no_overlap_point,c_d_no_overlap_point_weight).
soft_weight(c_d_no_overlap_bar,c_d_no_overlap_bar_weight).
soft_weight(c_d_no_overlap_line,c_d_no_overlap_line_weight).
soft_weight(c_d_no_overlap_area,c_d_no_overlap_area_weight).
soft_weight(c_d_no_overlap_text,c_d_no_overlap_text_weight).
soft_weight(c_d_no_overlap_tick,c_d_no_overlap_tick_weight).
soft_weight(d_d_point,d_d_point_weight).
soft_weight(d_d_text,d_d_text_weight).
soft_weight(d_d_rect,d_d_rect_weight).
soft_weight(continuous_x,continuous_x_weight).
soft_weight(continuous_y,continuous_y_weight).
soft_weight(continuous_color,continuous_color_weight).
soft_weight(continuous_size,continuous_size_weight).
soft_weight(continuous_text,continuous_text_weight).
soft_weight(ordered_x,ordered_x_weight).
soft_weight(ordered_y,ordered_y_weight).
soft_weight(ordered_color,ordered_color_weight).
soft_weight(ordered_size,ordered_size_weight).
soft_weight(ordered_text,ordered_text_weight).
soft_weight(ordered_row,ordered_row_weight).
soft_weight(ordered_column,ordered_column_weight).
soft_weight(nominal_x,nominal_x_weight).
soft_weight(nominal_y,nominal_y_weight).
soft_weight(nominal_color,nominal_color_weight).
soft_weight(nominal_shape,nominal_shape_weight).
soft_weight(nominal_text,nominal_text_weight).
soft_weight(nominal_row,nominal_row_weight).
soft_weight(nominal_column,nominal_column_weight).
soft_weight(nominal_detail,nominal_detail_weight).
soft_weight(interesting_x,interesting_x_weight).
soft_weight(interesting_y,interesting_y_weight).
soft_weight(interesting_color,interesting_color_weight).
soft_weight(interesting_size,interesting_size_weight).
soft_weight(interesting_shape,interesting_shape_weight).
soft_weight(interesting_text,interesting_text_weight).
soft_weight(interesting_row,interesting_row_weight).
soft_weight(interesting_column,interesting_column_weight).
soft_weight(interesting_detail,interesting_detail_weight).
soft_weight(aggregate_count,aggregate_count_weight).
soft_weight(aggregate_sum,aggregate_sum_weight).
soft_weight(aggregate_mean,aggregate_mean_weight).
soft_weight(aggregate_median,aggregate_median_weight).
soft_weight(aggregate_min,aggregate_min_weight).
soft_weight(aggregate_max,aggregate_max_weight).
soft_weight(aggregate_stdev,aggregate_stdev_weight).
soft_weight(value_point,value_point_weight).
soft_weight(value_bar,value_bar_weight).
soft_weight(value_line,value_line_weight).
soft_weight(value_area,value_area_weight).
soft_weight(value_text,value_text_weight).
soft_weight(value_tick,value_tick_weight).
soft_weight(value_rect,value_rect_weight).
soft_weight(summary_point,summary_point_weight).
soft_weight(summary_bar,summary_bar_weight).
soft_weight(summary_line,summary_line_weight).
soft_weight(summary_area,summary_area_weight).
soft_weight(summary_text,summary_text_weight).
soft_weight(summary_tick,summary_tick_weight).
soft_weight(summary_rect,summary_rect_weight).
soft_weight(value_continuous_x,value_continuous_x_weight).
soft_weight(value_continuous_y,value_continuous_y_weight).
soft_weight(value_continuous_color,value_continuous_color_weight).
soft_weight(value_continuous_size,value_continuous_size_weight).
soft_weight(value_continuous_text,value_continuous_text_weight).
soft_weight(value_discrete_x,value_discrete_x_weight).
soft_weight(value_discrete_y,value_discrete_y_weight).
soft_weight(value_discrete_color,value_discrete_color_weight).
soft_weight(value_discrete_shape,value_discrete_shape_weight).
soft_weight(value_discrete_size,value_discrete_size_weight).
soft_weight(value_discrete_text,value_discrete_text_weight).
soft_weight(value_discrete_row,value_discrete_row_weight).
soft_weight(value_discrete_column,value_discrete_column_weight).
soft_weight(summary_continuous_x,summary_continuous_x_weight).
soft_weight(summary_continuous_y,summary_continuous_y_weight).
soft_weight(summary_continuous_color,summary_continuous_color_weight).
soft_weight(summary_continuous_size,summary_continuous_size_weight).
soft_weight(summary_continuous_text,summary_continuous_text_weight).
soft_weight(summary_discrete_x,summary_discrete_x_weight).
soft_weight(summary_discrete_y,summary_discrete_y_weight).
soft_weight(summary_discrete_color,summary_discrete_color_weight).
soft_weight(summary_discrete_shape,summary_discrete_shape_weight).
soft_weight(summary_discrete_size,summary_discrete_size_weight).
soft_weight(summary_discrete_text,summary_discrete_text_weight).
soft_weight(summary_discrete_row,summary_discrete_row_weight).
soft_weight(summary_discrete_column,summary_discrete_column_weight).
soft_weight(stack_zero,stack_zero_weight).
soft_weight(stack_normalize,stack_normalize_weight).
soft_weight(x_y_fields_order,x_y_fields_order_weight). %trubens
soft_weight(rect_no_agg,rect_no_agg_weight).
% Minimize the feature weight

#minimize { WD,F,V,Q: soft_weight(F,WD), soft(F,V,Q), not base(V) }.

% #minimize { W@2,F,V,Q: soft_weight(F,W), soft(F,V,Q), not base(V) }.
% #minimize { W@1,F,V1,V2,A,B: compare_weight(F,W), compare(F,V1,V2,A,B) }.
% ====== Output ======

#show data/1.

#show mark/2.

#show view/1.
#show base/1.
#show encoding/2.

#show type/3.
#show channel/3.
#show field/3.
#show aggregate/3.
#show bin/3.
#show stack/2.

#show log/2.
#show zero/2.

#show soft/3.
#show compare/5.

#show soft_weight(N,W) : soft(N,_,_), soft_weight(N,W).
#show compare_weight(N,W) : compare(N,_,_,_,_), compare_weight(N,W).


#include "../../../draco-fk/asp/compare.lp".
#include "../../../draco-fk/asp/assign_compare_weights.lp".
#include "../../../draco-fk/asp/compare_hard.lp".
#include "../../../draco-fk/asp/compare_weights.lp".
#include "../../../draco-fk/asp/topk-py.lp".


view(v_v).
num_rows(406).

fieldtype("Name",string).
cardinality("Name", 311).
fieldtype("Miles_per_Gallon",number).
cardinality("Miles_per_Gallon", 130).
fieldtype("Cylinders",number).
cardinality("Cylinders", 5).
fieldtype("Displacement",number).
cardinality("Displacement", 83).
fieldtype("Horsepower",number).
cardinality("Horsepower", 94).
fieldtype("Weight_in_lbs",number).
cardinality("Weight_in_lbs", 356).
fieldtype("Acceleration",number).
cardinality("Acceleration", 96).
fieldtype("Year",number).
cardinality("Year", 12).
fieldtype("Origin",string).
cardinality("Origin", 3).

encoding(v_v,e0).
encoding(v_v,e1).
:- not field(v_v,E,"Displacement") : encoding(v_v,E).
:- not field(v_v,E,"Horsepower") : encoding(v_v,E).

%*
Important rules

Forces encodings to be in field alphabetical order. No idea why, probably for debug
:- field(V,E1,F1), field(V,E2,F2), E1 > E2, F1 <= F2.

Tiebreaker to keep x and y field assignments in alphabetical order
soft(x_y_fields_order,V) :- field(V,EX,F1), field(V,EY,F2), channel(V,EX,x), channel(V,EY,y), F1 > F2.

These alternates will work if relax above constraints
:- not field(v_v,e0,"Displacement").
:- not field(v_v,e1,"Horsepower").
field(v_v,e0,"Horsepower").
field(v_v,e1,"Displacement").
*%

% this works if relax E/F hard and tie breaker soft



% This works for first and some other models, but not all.
%soft(disp_x):- channel(v_v,e0,x), not channel(v_v,e0,y), channel(v_v,e1,y), not channel(v_v,e1,x).
%#const disp_x_weight = 100.
%soft_weight(disp_x, disp_x_weight).

% Hard constrait works a treat
%:- channel(v_v,e0,x), not channel(v_v,e0,y), channel(v_v,e1,y), not channel(v_v,e1,x).

% Explicit soft constraint also works a treat - now can't reproduce!
%:~ channel(v_v,e0,x), not channel(v_v,e0,y), channel(v_v,e1,y), not channel(v_v,e1,x). [100]
%:~ channel(v_v,e0,y), channel(v_v,e1,x). [100] % Wed - This works
%:~ channel(v_v,e0,y), channel(v_v,e1,x). [100] % Wed - This works
%:~ channel(v_v,e0,x), channel(v_v,e1,y), is_c_c(v_v). [100] % Wed - this works but needs a more careful look
%:~ channel(V,e0,y), channel(V,e1,x), is_c_c(V). [100] % Wed - this works, but still #4 differs in one case

%* THIS WORKS BUT NOT STANDARD TEMPLATE FORM FOR, AND A LITTLE WORRIED ABOUT is_c_c
field(v_v,e0,"Horsepower").
field(v_v,e1,"Displacement").
soft(disp_hp,V):- channel(V,e0,x), channel(V,e1,y), is_c_c(V).
#const disp_hp_weight = 100.
soft_weight(disp_hp, disp_hp_weight).
*%

%* THIS WORKS BUT without the hard field rule, the standard form expands unecessary combinations
% of encoding and field which has no impact on the final visualisation.
% Might be better to take our approach above to assign fields to encodings.
:- not field(v_v,E,"Displacement") : encoding(v_v,E).
:- not field(v_v,E,"Horsepower") : encoding(v_v,E).
soft(disp_hp,V):- channel(V,E1,y), field(V, E1, "Displacement"), channel(V,E2,x), field(V, E2, "Horsepower"), is_c_c(V).
#const disp_hp_weight = 100.
soft_weight(disp_hp, disp_hp_weight).
*%

%clingo --outf=2 --quiet=1,2,2 --seed=0
%clingo --outf=2 --quiet=1,2,2 --seed=0 --opt-mode=OptN --models=5
