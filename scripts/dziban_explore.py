from dziban.mkiv import Chart
from draco.run import run as draco
from vega_datasets import data
import json


def print_draco_result(r, title):
    print(f'\n\n{title}')
    print('vl spec    :', json.dumps(r.as_vl(Chart.DEFAULT_NAME)))
    print('cost       :', r.cost)
    print('violations :', json.dumps(r.violations))
    print('weights    :', json.dumps(r.draco_weights))


def get_cars_asp():

    ch = Chart(data('cars'))
    ch = ch.field('Horsepower', 'Displacement')
    qu = ch._get_full_query()
    for l in qu:
        print(l)


if __name__ == "__main__":

    # get_cars_asp()
    # exit(1)

    gapminder = data('gapminder')
    chart = Chart(gapminder)
    schema = chart._get_full_query()
    print('\n\n---- HERE IS THE DEFAULT VIEW AND SCHEMA ----')
    for l in schema:
        print(l)

    gapminder1 = Chart(gapminder).field('pop', scale='zero').field('life_expect', scale='zero')
    # get the default view and schema asp.
    print('\n\n---- HERE IS THE DEFAULT VIEW, SCHEMA PLUS THE QUERY ----')
    query = gapminder1._get_full_query()
    for l in query:
        print(l)

    print('\n\n---- HERE IS THE VL FOR THE OPTIMAL MODEL ----')
    vl = gapminder1._get_vegalite()
    vl_json = json.dumps(vl)
    print(vl_json)

    #  r = gapminder1._get_render() # for display in Jupyter

    # call Draco directly with the query, for a single optimal cold recommendation
    result = draco(query)
    print_draco_result(result, '---- HERE IS THE SINGLE_RESULT DIRECT FROM DRACO ----')

    # call draco to get top 5 models from query
    results = draco(query, topk=True, k=5, silence_warnings=True)
    print('\n\n---- HERE ARE RESULTS FROM topk=5 ----')
    for i, result in enumerate(results):
        print_draco_result(result, f'model {i+1}')

    # try explicit field to encoding assignments in query
    query_expl = [
        'encoding(v_v,e0).',
        'encoding(v_v,e1).',
        ':- not field(v_v,e0,"pop").',
        #  ':- field(v_v,e0,"pop"), not zero(v_v,e0).',
        ':- not field(v_v,e1,"life_expect").'
        #  ':- field(v_v,e1,"life_expect"), not zero(v_v,e1).'
    ]
    query = schema + query_expl
    results = draco(query, topk=True, k=5, silence_warnings=True)
    print('\n\n---- HERE ARE topk=5 RESULTS FROM EXPLICIT QUERY ----')
    for i, result in enumerate(results):
        print_draco_result(result, f'model {i+1}')

    pass
