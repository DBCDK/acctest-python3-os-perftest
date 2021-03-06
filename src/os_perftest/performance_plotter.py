#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-

import sys
import datetime
import re
import logging
from operator import itemgetter

import os_perftest.performance_report as report
import os_perftest.config_parser as parser
import os_perftest.performance_dumper as dumper

COLORS = ["b", "y", "orange", "m", "r", "k", "g", "c" ]

logger = logging.getLogger("dbc." + __name__)

def plot(ini_file, main_plot, file_folder='performance-report' ):
    logger.info("Plot configured values. ini_file='%s', main_plot='%s', file_folder='%s'", ini_file, main_plot, file_folder)
    graphs = parser.parse_config(ini_file)
    pr = report.PerformanceReport( file_folder )

    for graph in graphs:
        pr.plot_data( graph["name"], graph["description"], graph["unit"], graph["timestamps"], *graph["lines"] )

    pr.create_report( plot_name=main_plot )

def _create_graph(name, description, unit, timestamps):
    graph = { "name": name,
              "description": description,
              "unit": unit,
              "timestamps": list(map(datetime.datetime.fromtimestamp, timestamps)),
              "lines": []}
    return graph

def _create_line(name, values, precision):
    if precision == 0:
        values = list(map(int, values))
    return [None, name, values, precision]

def _update_line_colors(lines):
    i = 0
    for line in lines:
        line[0] = COLORS[i % (len(COLORS)-1)]
        i += 1
    return lines

def _has_values(value_list):
    if value_list is not None:
        for value in value_list:
            if str(value).isdigit():
                return True
    return False

def _create_count_graphs(mbeans):
    graphs = []
    for key in mbeans:
        logger.debug("Create count graph for %s", key)

        mbean = mbeans[key]
        timestamps = mbean.get('timestamp')
        lines = []
        for key in mbean['value']:
            values = mbean['value'][key]
            if _has_values(values):
                logger.debug("values %s", values)
                if 'Count' in key:
                    lines.append(_create_line('Count', values, 0))
                elif 'requests' in key:
                    lines.append(_create_line('Count', values, 0))

        if len(lines) > 0:
            graph = _create_graph('Count-' + mbean['clean-name'], 'counts', "milliseconds", timestamps)
            graph['lines'] = _update_line_colors(lines)
            graphs.append(graph)
        else:
            logger.debug("Skip 0 value for %s", key)


    logger.debug("Create %s graphs", len(graphs))
    return graphs

def _create_percentile_graphs(mbeans):
    graphs = []

    for key in mbeans:
        mbean = mbeans[key]
        timestamps = mbean.get('timestamp')
        lines = []
        for key in mbean['value']:
            values = mbean['value'][key]
            if _has_values(values):
                if '50th' in key:
                    lines.append(_create_line('50th percentile', values, 2))
                elif '75th' in key:
                    lines.append(_create_line('75th percentile', values, 2))
                elif '95th' in key:
                    lines.append(_create_line('95th percentile', values, 2))
                elif '99th' in key and not '999th' in key:
                    lines.append(_create_line('99th percentile', values, 2))
                elif 'median' in key:
                    lines.append(_create_line('50th percentile', values, 2))
                elif 'avgTimePerRequest' == key:
                    lines.append(_create_line('Mean', values, 2))
                elif 'Mean' == key:
                    lines.append(_create_line('Mean', values, 2))
                elif 'Min' == key:
                    lines.append(_create_line('Min', values, 2))
                elif 'Max' == key:
                    lines.append(_create_line('Max', values, 2))

        if len(lines) > 0:
            graph = _create_graph('Timings-' + mbean['clean-name'], 'timings', "milliseconds", timestamps)
            graph['lines'] = _update_line_colors(sorted(lines, key=itemgetter(1)))
            graphs.append(graph)

    return graphs

def _is_mbean(element):
        if 'value' in element:
            return True
        return False

def _fetch_mbeans(element, mbeans):

    if not isinstance(element, dict):
        return

    if _is_mbean(element):
        mbean_name = element['request']['mbean']
        mbean_dict = mbeans.get(mbean_name)
        if mbean_dict is None:
            mbean_dict = {}
            mbean_dict['name'] = mbean_name
            mbean_dict['clean-name'] = re.search(r'(.+=[\w\.]+)', mbean_name).group(1).replace('/', '-').replace(':', '-')
            mbean_dict['timestamp'] = []
            mbean_dict['value'] = {}
            #print(mbean_dict['clean-name'])
        mbeans[mbean_name] = mbean_dict
        mbean_dict['timestamp'].append(element.get('timestamp'))

        for key in element['value']:
            value_list = mbean_dict['value'].get(key)
            if value_list is None:
                value_list = []
                mbean_dict['value'][key] = value_list
            value_list.append(element['value'][key])

        return

    for key in element:
        _fetch_mbeans(element[key], mbeans)

def plot_dump(*dump_file):
    plot_dump_to('performance-report', *dump_file)

def plot_dump_to(filefolder, *dump_file):

    logger.info("Plotting graphs to folder '%s'", filefolder)

    mbeans = {}
    for file in dump_file:
        pd = dumper.MBeanDumper(file)
        dump = pd._read_dump()

        for element in dump:
            _fetch_mbeans(element, mbeans)

    pr = report.PerformanceReport(filefolder)
    graphs = []

    # Create a graph for each mbean, which has count data
    graphs.extend(_create_count_graphs(mbeans))

    # Create a graph for each mbean, which has percentile data
    graphs.extend(_create_percentile_graphs(mbeans))

    graphs_count = len(graphs)
    if graphs_count == 0:
        logger.warning("Plotting no graphs for '%s'. All values are 0", filefolder)
    else:
        logger.warning("Plotting %s graphs", graphs_count)
        for graph in sorted(graphs, key=lambda x: x['name']):
            pr.plot_data(graph["name"], graph["description"], graph["unit"], graph["timestamps"], *graph["lines"])

        pr.create_report()

if __name__ == '__main__':

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python %s ini_file [main_plot_name] [file_folder]" % sys.argv[0])
        sys.exit(1)
    
    ini_file = sys.argv[1]
    main_plot = None
    if len(sys.argv) > 2:
        main_plot = sys.argv[2]

    file_folder = 'performance-report'
    if len(sys.argv) > 3:
        file_folder = sys.argv[3]

    plot(ini_file, main_plot, file_folder)
    # plot_dump(ini_file)
