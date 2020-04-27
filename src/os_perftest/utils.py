#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-

import datetime
import logging
import time
from os_perftest.performance_dumper import MBeanDumper
from os_perftest.performance_test import NullHandler


logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())

def dump_statistics(filename, *mBean_pair):
        """ Dumps mbean statistics to file (through jolokia)"""
        logger.info("Dumping performance statistics to file %s" % filename)
        mbd = MBeanDumper(filename)

        mbd.dump(*mBean_pair)

def format_traceback(exc_info, error):
    """ Formats traceback, for easy reading """
    import traceback
    exc_tb = traceback.extract_tb(exc_info[2])
    tb = traceback.format_list(exc_tb)
    tb = [[x] for x in tb]

    formatted_traceback = []
    for entry in tb:
        for fentry in [x for x in entry[0].split("\n") if x != '']:
            formatted_traceback.append(fentry)

    formatted_traceback.insert(0, "Traceback (most recent call last):")
    formatted_traceback.append("%s: %s" % (error.__class__.__name__, str(error)))
    return "\n".join(formatted_traceback)

def test_executor(run_time):
    """ Executes the performance test """
    start = datetime.datetime.now()

    if run_time:
            logger.info("Running test for %s seconds" % run_time)
            time.sleep(run_time)
    else:
        input("\nPress Enter to shutdown...")

    delta = datetime.datetime.now() - start
    logger.info('test ran for %s seconds' % delta.seconds)

def setup_logger(verbose=False):
    """ Sets up logger instance"""
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s",
                        filename='run_perf_test.log',
                        filemode='w')
    logger = logging.getLogger('')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    if verbose:
        ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
