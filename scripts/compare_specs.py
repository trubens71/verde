import src.compare as vcomp
import json

file_a = '../laboratory/trial_03/vegalite/trial_03.exp_01_baseline_m25_c036_vl.json'
file_b = '../laboratory/trial_03/vegalite/trial_03.exp_01_verde_m19_c035_vl.json'
specs = []

for file in [file_a, file_b]:
    with open(file) as f:
        spec = json.load(f)
        spec.pop('title', None)
        specs.append(spec)

print (vcomp.compare_specs(specs[0], specs[1]))