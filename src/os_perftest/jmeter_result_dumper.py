#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from lxml import etree
import json
import logging
import math
import os
from .performance_report import PerformanceReport
from .performance_report import gen_dates


logger = logging.getLogger(__name__)

def calculate_values(base_lst, percentiles=None):

    result = {}
    result['samples'] = len(base_lst)
    result['min'] = min(base_lst)
    result['max'] = max(base_lst)
    result['mean'] = sum(base_lst) / result['samples']
    square_dif = [(x - result['mean'])**2 for x in base_lst]
    result['standard-deviation'] = math.sqrt(sum(square_dif) / len(square_dif))
    result['percentiles'] = {}
    if percentiles is not None:
        sorted_lst = sorted(base_lst)
        for p in percentiles:
            result['percentiles'][p] = sorted_lst[int((p / 100.0) * len(sorted_lst)-1)]

    return result


def harvest_values_from_jtl_file(jtl_file):

    logger.debug('Harvesting raw values from jtl file %s' % jtl_file)
    time = []
    latency = []
    xml = etree.parse(jtl_file)
    for node in xml.xpath('/testResults/httpSample'):
        time.append(int(node.get('t')))
        latency.append(int(node.get('lt')))

    logger.debug("Calculating derived values")
    return {'time': calculate_values(time, percentiles=[10,90]),
            'latency': calculate_values(latency, percentiles=[10,90])}



def collect_and_append_jtl_results_to_dump_file(dump_file, jtl_file, strict=False):

    data = []
    if os.path.exists(dump_file):
        logger.debug('loading previous dump from %s' % dump_file)
        with open(dump_file) as fh:
            data = json.load(fh)
    elif strict:
        err_msg = 'Dumpfile %s does not exists' % dump_file
        logger.error(err_msg)
        raise runtimeError(err_msg)

    # Truncate data to 20 weeks/140 days
    data = data[-140:]

    data.append(harvest_values_from_jtl_file(jtl_file))

    logger.debug('entries in new dump %s' % len(data))
    with open(dump_file, 'w') as fh:
        logger.debug('saving dump to %s' % dump_file)
        json.dump(data, fh, indent=2)



def order_values(dump_file, key):
    colors = ['b', 'g', 'c', 'y', 'orange', 'm', 'r']
    values = []
    samples, this_slice = slice_data_dump(dump_file, key)
    for i, (k, v) in enumerate(this_slice.items()):
        values.append((colors[i], k, v, 0))
    return samples, values


def make_performance_report(dump_file):

    time_samples, time_data = order_values(dump_file, 'time')
    latency_samples, latency_data = order_values(dump_file, 'latency')

    values = [("Time", "request time (%s samples)" % time_samples[-1], "milliseconds", time_data),
              ("Latency", "request latency (%s samples)" % latency_samples[-1], "milliseconds", latency_data)]


    pr = PerformanceReport('performance-report')

    for name, description, unit, data in values:
        dates = gen_dates(len(data[0][2]))
        pr.plot_data(name, description, unit, dates, *data)

    pr.create_report(plot_name="Time")



def slice_data_dump(dump_file, value):

    data = None

    with open(dump_file) as fh:
        data = json.load(fh)

    if data is None:
        raise RuntimeError("No data found")

    entry = [x[value] for x in data]
    sliced_data = {}
    samples = None
    for key in list(entry[0].keys()):
        if key == 'samples':
            samples = [x[key] for x in entry]
        elif key == 'percentiles':
            for p in list(entry[0][key].keys()):
                sliced_data["%s_percentile" % p] = [x[key][p] for x in entry]
        else:
            sliced_data[key] = [x[key] for x in entry]

    return samples, sliced_data


def main():
    
    jtl_file, dump_file, plot_dump = cli()
    collect_and_append_jtl_results_to_dump_file(dump_file, jtl_file)

    if plot_dump:
        make_performance_report(dump_file)


def cli():
    logging.basicConfig(filename='jmeter-result_dumper.log', level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)

    usage_msg = "%prog [options] jtl-result-file"

    from optparse import OptionParser
    parser = OptionParser(usage=usage_msg + '\n')

    default_dump_file = "jtl-performance-dump.json"

    parser.add_option("-d", "--dump-file", type="string", action="store", dest="dump_file", default=default_dump_file,
                      help="File to dump/append result to. default is '%s'" % default_dump_file)

    parser.add_option("-p", "--plot-dump", action="store_true", dest="plot_dump", default=False,
                      help="Creates performance report based on plot")

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('Need jtl result file')

    if not os.path.exists(args[0]):
        parser.error('jtl result file "%s" does not exist' % args[0])

    return args[0], options.dump_file, options.plot_dump

if __name__ == '__main__':
    main()
