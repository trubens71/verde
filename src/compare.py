import logging
from shapely.geometry import LineString
import os
import pandas as pd
import altair as alt
from altair import datum
import datetime
import json
import src.utils as vutils
import dictdiffer

diff_set = set()


def compare_baseline_to_verde(trial_id, directory, baseline_results, verde_results,
                              baseline_label='baseline', verde_label='verde'):
    """
    Identify the differences between the baseline vis set and the verde vis set:
    - Vis specs present in one set but not the other
    - Identical Vis specs but with different rankings or different costs
    Go on to produce an exploratory visualisation to present the comparison.
    :param verde_label:
    :param baseline_label:
    :param trial_id:
    :param directory:
    :param baseline_results:
    :param verde_results:
    :return:
    """

    # will later augment our results with cross reference of matches between sets, so initialise all as None
    for result_set in [baseline_results, verde_results]:
        for result in result_set:
            result['matches'] = None

    # conduct a pairwise comparison of specs in each set.
    b_v_pairs = [(b, v) for b, _ in enumerate(baseline_results) for v, _ in enumerate(verde_results)]
    matches = []
    for b, v in b_v_pairs:
        # remove the title before comparing the guts of the vl spec
        b_cmp = baseline_results[b]['vl']
        b_cmp.pop('title', None)
        v_cmp = verde_results[v]['vl']
        v_cmp.pop('title', None)
        match_type = compare_specs(b_cmp, v_cmp)
        if match_type:
            baseline_results[b]['matches'] = v
            verde_results[v]['matches'] = b
            matches.append({'b_rank': b,
                            'b_cost': baseline_results[b]['cost'],
                            'v_rank': v,
                            'v_cost': verde_results[v]['cost'],
                            'crossed': 'not',
                            'match_type': match_type})

    logging.debug(f'found {len(diff_set)} spec diffs')
    # some summary stats
    b_not_in_v = [baseline_results[i]['matches'] for i,_ in enumerate(baseline_results) ].count(None)
    v_not_in_b = [verde_results[i]['matches'] for i,_ in enumerate(verde_results) ].count(None)
    logging.info(f'{len(matches)} matching visualisations between baseline and verde '
                 f'{len(matches)/len(baseline_results):.1%}')
    logging.info(f'{b_not_in_v} baseline visualisations not in verde')
    logging.info(f'{v_not_in_b} verde visualisations not in verde')

    # identify crossed edges which signifies a different ranking between baseline and verde
    # inspect the matches pairwise and tag them if they intersect.
    match_idx_pairs = [(m, n) for m, _ in enumerate(matches) for n, _ in enumerate(matches) if m < n]
    for m, n in match_idx_pairs:
        line_m = LineString([(0, matches[m]['b_rank']), (1, matches[m]['v_rank'])])
        line_n = LineString([(0, matches[n]['b_rank']), (1, matches[n]['v_rank'])])
        if line_m.intersects(line_n):
            for i in [m, n]:
                if matches[i]['b_cost'] == matches[i]['v_cost']:
                    matches[i]['crossed'] = 'with_equal_cost'
                else:
                    matches[i]['crossed'] = 'with_different_cost'

    # write the match file to csv for exploratory visualisation
    if matches:
        df = pd.DataFrame(matches)
        df['match'] = df.index
        df = df.melt(id_vars=['match', 'match_type', 'crossed', 'b_cost', 'v_cost'], var_name='set', value_name='rank')
        df.set = df.set.str.replace('b_rank', baseline_label)
        df.set = df.set.str.replace('v_rank', verde_label)
        match_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_match.csv')
        logging.info(f'writing comparison matches to {match_csv_file}')
        df.to_csv(match_csv_file, index=False)
    else:
        logging.warning(f'no matches found between {baseline_label} and {verde_label}')
        match_csv_file = None

    # simplify and union the visualisation model (instance) data
    df_baseline = pd.DataFrame(baseline_results)
    df_baseline['set'] = baseline_label
    df_baseline['rank'] = df_baseline.index
    df_verde = pd.DataFrame(verde_results)
    df_verde['set'] = verde_label
    df_verde['rank'] = df_verde.index
    df = pd.concat([df_baseline, df_verde])
    df['has_match'] = df.matches.notnull()
    df.vl_spec_file = df.vl_spec_file.apply(lambda x: os.path.basename(x))
    vis_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_model.csv')
    logging.info(f'writing comparison models to {vis_csv_file}')
    df.to_csv(vis_csv_file, index=False)

    # create violation data for the exploratory vis
    violation_records = []
    for _, row in df.iterrows():
        violations = dict(row.violations)
        for violation in violations.keys():
            record = violations[violation]
            record['violation'] = violation
            record['set'] = row['set']
            record['rank'] = row['rank']
            violation_records.append(record)
    df_violations = pd.DataFrame(violation_records)
    df_violations = df_violations[['set', 'rank', 'violation', 'num', 'weight', 'cost_contrib']]
    violations_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_violations.csv')
    logging.info(f'writing comparison violations to {violations_csv_file}')
    df_violations.to_csv(violations_csv_file, index=False)

    # create prop data for the exploratory vis
    prop_records = []
    for _, row in df.iterrows():
        for prop in row.props:
            record = {'set': row['set'], 'rank': row['rank'], 'prop': prop}
            prop_records.append(record)
    df_props = pd.DataFrame(prop_records)
    props_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_props.csv')
    logging.info(f'writing comparison props to {props_csv_file}')
    df_props.to_csv(props_csv_file, index=False)

    # produce the exploratory vis and a viewer to support hyperlink click through
    create_exploratory_visualisation(trial_id, directory, vis_csv_file, match_csv_file,
                                     violations_csv_file, props_csv_file,
                                     baseline_label, verde_label)
    # A generic html file to present a single vl spec passed as a parameter from the exploratory vis by href
    write_single_vis_viewer(trial_id, directory)


def find_crossed_matches(matches):
    for i, _ in enumerate(matches):
        matches[i]['crossed'] = False

    match_idx_pairs = [(m, n) for m, _ in enumerate(matches) \
                       for n, _ in enumerate(matches) if m < n]

    for m, n in match_idx_pairs:
        if (matches[n]['a_rank'] > matches[m]['a_rank'] and matches[n]['b_rank'] < matches[m]['b_rank']) or \
                (matches[n]['a_rank'] < matches[m]['a_rank']
                 and matches[n]['b_rank'] > matches[m]['b_rank']):
            matches[m]['crossed'] = True
            matches[n]['crossed'] = True

    return matches


def compare_specs(b_spec, v_spec):
    """
    compare two specs, taking into account differences that we introduces (e.g. ordinal sorts in rule 03)
    :param b_spec:
    :param v_spec:
    :return:
    """

    match_type = None
    verde_introduced_diffs = False

    if b_spec == v_spec:
        return 'exact'

    dict_diff = dictdiffer.diff(b_spec, v_spec)
    verde_introduced_diffs = True

    for diff in dict_diff:
        # rule 03 introduced ordinal sort
        if diff[0] == 'add' and diff[2][0][0] == 'sort':
            pass
        # rule 04 introduced a colour channel encoding
        elif diff[0] == 'add' and diff[1] == 'encoding' and len(diff[2][0]) == 1 and diff[2][0][0] == 'color':
            logging.debug('')
        # rule 04 added a scale to a colour encoding
        elif diff[0] == 'add' and diff[1] == 'encoding.color.scale':
            pass
        elif diff[0] == 'remove' and diff[1] == 'encoding.color.scale':
            pass
        elif diff[0] == 'add' and diff[1] == 'encoding' and diff[2][0][0] == 'color' and ("{'scheme':" in str(diff)):  # yuck!
            logging.debug('')
        # rule 04 changes mark from shorthand to longhand
        elif diff[0] == 'change' and diff[1] == 'mark' and isinstance(diff[2][1], dict):
            if diff[2][0] == diff[2][1]['type']:  # ok if mark types are the same
                pass
        else:
            verde_introduced_diffs = False
            diff_set.add(str(diff))
            break

    if verde_introduced_diffs:
        match_type = 'verde_addition'

    return match_type


def write_single_vis_viewer(trial_id, directory):

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
        <!-- Import Vega & Vega-Lite (does not have to be from CDN) -->
        <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
        <!-- Import vega-embed -->
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    </head>
    <body>
    
    <script>
        var url_string = window.location.href
        var url = new URL(url_string);
        var vl_json = url.searchParams.get("vl_json");
        //console.log(c);
    </script>
    
    <div id="vis"></div>
    <script type="text/javascript">
        var spec = vl_json;
        vegaEmbed('#vis', spec).then(function(result) {}).catch(console.error);
    </script>
    
    </body>
    </html>    
    """

    with open(os.path.join(directory, 'vegalite', f'{trial_id}_view_one_vl.html'), 'w') as f:
        f.write(html)


def create_exploratory_visualisation(trial_id, directory, vis_data_file, match_data_file,
                                     violations_data_file, props_data_file,
                                     baseline_label='baseline', verde_label='verde'):

    vl_viewer = f'{trial_id}_view_one_vl.html?vl_json='

    # common data and transforms for first layer with marks for each vis model
    base = alt.Chart(os.path.basename(vis_data_file)).transform_calculate(
        rank="format(datum.rank,'03')",
        link=f"'{vl_viewer}' + datum.vl_spec_file"
    ).properties(
        width=250,
        height=alt.Step(30),
        title='visualisation rankings'
    )

    # add a selectable square for each vis model
    select_models = alt.selection_multi(fields=['set', 'rank'])
    select_brush = alt.selection_interval()
    squares = base.mark_square(
        size=150
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('rank:O', axis=alt.Axis(title=None)),
        tooltip=['set:N', 'rank:N', 'cost:Q'],
        opacity=alt.Opacity('has_match:O', legend=None),
        color=alt.condition(select_models | select_brush, alt.value('steelblue'), alt.value('lightgray'))
    ).add_selection(
        select_models, select_brush
    ).interactive()

    # add a small circle with the hyperlink to the actual vis.
    # Shame that xoffset is not an encoding channel, so we have to do in two steps...
    def make_circles(vis_set, offset):
        return base.transform_filter(
            datum.set == vis_set
        ).mark_circle(
            size=25,
            xOffset=offset,
        ).encode(
            alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
            alt.Y('rank:O'),
            tooltip=['link:N'],
            href='link:N',
            color=alt.condition(select_models | select_brush, alt.value('steelblue'), alt.value('lightgray'))
        ).interactive()

    baseline_circles = make_circles(baseline_label, -15)
    verde_circles = make_circles(verde_label, 15)

    # next layer is match lines, handle case of no matches
    if match_data_file:
        col_domain = ['not', 'with_equal_cost', 'with_different_cost']
        col_range_ = ['steelblue', 'green', 'red']
        match_lines = alt.Chart(os.path.basename(match_data_file)).mark_line().transform_calculate(
            rank="format(datum.rank,'03')"
        ).encode(
            alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
            alt.Y('rank:O'),
            detail=['match:N', 'match_type:N'],
            strokeDash=alt.StrokeDash('match_type:N',
                                      scale=alt.Scale(
                                          domain=['verde_addition', 'exact'],
                                          range=[[5, 4], [1, 0]]
                                      ),
                                      legend=alt.Legend(orient='bottom')),
            color=alt.condition(select_models | select_brush,
                                alt.Color('crossed:N', scale=alt.Scale(domain=col_domain, range=col_range_),
                                          legend=alt.Legend(orient='bottom')),
                                alt.value('lightgray'))
        )
    else:
        match_lines = None

    # rules to connect models with the same cost
    cost_rules = base.mark_rule(
        strokeWidth=2
    ).transform_aggregate(
        min_rank='min(rank)',
        max_rank='max(rank)',
        groupby=['set', 'cost']
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('min_rank:O'),
        alt.Y2('max_rank:O'),
        color=alt.condition(select_models | select_brush, alt.value('steelblue'), alt.value('lightgray')),
        tooltip=['cost:Q', 'min_rank:O', 'max_rank:O']
    ).interactive()

    rank_chart = baseline_circles + verde_circles

    if match_lines:
        rank_chart = rank_chart + match_lines

    rank_chart = rank_chart + cost_rules + squares

    # chart to show violation occurrences and weights for selected vis models across sets
    def make_violation_chart(dimension, width_step):
        return alt.Chart(os.path.basename(violations_data_file)).mark_circle(
            color='red',
        ).transform_calculate(
            rank="format(datum.rank,'03')",
        ).transform_filter(
            select_models
        ).transform_filter(
            select_brush
        ).encode(
            x=alt.X(f'{dimension}:N', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
            y=alt.Y('violation:N', axis=alt.Axis(title=None)),
            size=alt.Size('num:Q', legend=None),
            opacity=alt.Opacity('weight:Q', scale=alt.Scale(range=[0, 1]), legend=None),
            tooltip=['set:N', 'rank:Q', 'violation:N', 'num:Q', 'weight:Q', 'cost_contrib:Q']
        ).properties(
            width=alt.Step(width_step),
            title=f'soft rule violations (x-{dimension})'
        ).interactive()

    violation_set_chart = make_violation_chart('set', 40)
    violation_rank_chart = make_violation_chart('rank', 30)

    # chart to show prop occurrences for selected vis models across sets
    def make_prop_chart(dimension, width_step):
        return alt.Chart(os.path.basename(props_data_file)).mark_circle(
            size=50,
            color='green'
        ).transform_calculate(
            rank="format(datum.rank,'03')"
        ).transform_filter(
            select_models
        ).transform_filter(
            select_brush
        ).encode(
            x=alt.X(f'{dimension}:N', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
            y=alt.Y('prop:N', axis=alt.Axis(title=None)),
            tooltip=['prop:N']
        ).properties(
            width=alt.Step(width_step),
            title=f'specification terms (x-{dimension})'
        ).interactive()

    prop_set_chart = make_prop_chart('set', 40)
    prop_rank_chart = make_prop_chart('rank', 30)

    # glue them all together
    top_chart = rank_chart | violation_set_chart | prop_set_chart
    bottom_chart = violation_rank_chart | prop_rank_chart
    chart = top_chart & bottom_chart
    # put a timestamp
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chart = chart.properties(
        title=f'{trial_id} {ts}'
    )

    file_name = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare.html')
    logging.info(f'writing comparison visualisation to {file_name}')
    chart.save(file_name)


if __name__ == "__main__":
    # an entry point to let us compare across two experiments, particularly two verde sets
    # Note that the vis will still refer to baseline and verde.
    logging = vutils.configure_logger('compare.log', logging.DEBUG)
    _trial_id = 'trial_01.verde_verde_exp_01_02'
    _directory = '../laboratory/trial_01'

    with open(f'{_directory}/trial_01.exp_01_verde_results.json') as f:
        _baseline_results = json.load(f)

    with open(f'{_directory}/trial_01.exp_02_verde_results.json') as f:
        _verde_results = json.load(f)

    # but in this case the match won't work because the data url will be different,
    # so we trust you know what you are doing and we will copy across the data url from
    # one set to the other.

    data_url = _baseline_results[0]['vl']['data']['url']
    for result in _verde_results:
        result['vl']['data']['url'] = data_url

    compare_baseline_to_verde(_trial_id, _directory, _baseline_results, _verde_results,
                              baseline_label='v_t1_e1', verde_label='v_t1_e2')