
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