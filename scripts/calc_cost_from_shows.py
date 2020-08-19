# this is quick hack to help some excel analysis
import re
from collections import defaultdict

shows = """
"view(v_v)",
"encoding(v_v,e0)",
"encoding(v_v,e1)",
"field(v_v,e0,\"Displacement\")",
"field(v_v,e1,\"Horsepower\")",
"soft(encoding,v_v,e0)",
"soft(encoding,v_v,e1)",
"soft(encoding_field,v_v,e0)",
"soft(encoding_field,v_v,e1)",
"soft_weight(encoding,0)",
"soft_weight(encoding_field,6)",
"channel(v_v,e0,x)",
"channel(v_v,e1,y)",
"bin(v_v,e1,10)",
"zero(v_v,e0)",
"type(v_v,e0,quantitative)",
"type(v_v,e1,quantitative)",
"mark(v_v,tick)",
"soft(orientation_binned,v_v,_placeholder)",
"soft(c_d_tick,v_v,_placeholder)",
"soft(bin,v_v,e1)",
"soft(type_q,v_v,e0)",
"soft(type_q,v_v,e1)",
"soft(continuous_x,v_v,e0)",
"soft(ordered_y,v_v,e1)",
"soft_weight(orientation_binned,2)",
"soft_weight(c_d_tick,0)",
"soft_weight(bin,2)",
"soft_weight(type_q,0)",
"soft_weight(continuous_x,0)",
"soft_weight(ordered_y,0)",
"""

shows = shows.replace('"', '')
shows = shows.split('\n')
print(shows)

reg_soft = re.compile(r'soft\((.*?),.*\)')
reg_weight = re.compile(r'soft_weight\((.*),(.*)\)')

violations = defaultdict(int)
weights = defaultdict(int)

for show in shows:
    if show.startswith('soft('):
        m = re.search(reg_soft, show)
        violations[m.group(1)] += 1
    if show.startswith('soft_weight('):
        m = re.search(reg_weight,show)
        weights[m.group(1)] = int(m.group(2))

print(violations)
print(weights)
cost = sum(violations[key]*weights[key] for key in violations)

print(f' (cost={cost})')


pass