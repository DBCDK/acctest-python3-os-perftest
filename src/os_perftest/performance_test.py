#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-

import datetime
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from configobj import ConfigObj

from os_python.common.utils.init_functions import log_fields
from os_python.common.utils.init_functions import die
from os_python.common.utils.cleanupstack import CleanupStack

import os_perftest.performance_report as performance_report
from os_perftest.performance_dumper import MBeanDumper
from os_perftest.performance_report import PerformanceReport
import os_perftest.performance_plotter as performance_plotter

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


class PerformanceTest:

    def on_service_start(self, name, service, configuration):
        pass

    def on_dump_statistics(self, services, configuration):
        pass

    def on_test_end(self, services, configuration):
        pass

    def on_services_stopped(self, configuration):
        pass

    def __init__(self, configuration):
        self.configuration = {'resource-folder': 'resources',
                             'build-folder': 'build',
                             'log-folder': 'logfiles',
                             'log-zip-file':'logs.zip'}

        self.configuration.update(configuration)
        self._setup_logger(configuration['verbose'])
        log_fields("Performance configuration", fields=configuration)

    def start(self):
        configuration = self.configuration

        self._delete_folders(configuration['build-folder'])
        services = self.create_services(configuration)
        self._run_performance_test(configuration, services)


    def _register_and_start_sevice(self, name, service, stack, log_folder):
        """ Register services on the stack, and starts them"""
        stack.addFunction(service.stop)
        stack.addFunction(self._save_service_logfiles, service, name, log_folder)
        stack.addFunction(logger.info, 'stopping %s' % name)
        service.start()

    def _run_performance_test(self, configuration, services):
        """ Run the performance test """
        if not os.path.exists(configuration['log-folder']):
            os.mkdir(configuration['log-folder'])

        stop_stack = CleanupStack.getInstance()

        try:
            for (name, service) in services:
                self._register_and_start_sevice(name, service, stop_stack, configuration['log-folder'])
                self.on_service_start(name, service, configuration)

            if configuration['run-time']:
                logger.info("Running test for %s seconds" % configuration['run-time'])
                if 'dump-every' in configuration and configuration['dump-every'] is not None:
                    now = lambda: datetime.datetime.now()
                    start = now()
                    end = now() + datetime.timedelta( 0, configuration['run-time'] )
                    while( now() < end ):
                        dump_start = now()
                        logger.debug("Dumping performance statistics")
                        self.on_dump_statistics(services, configuration )
                        duration =  now() - dump_start
                        sleep_time = int(configuration['dump-every']) - duration.seconds;
                        logger.debug("Sleeping %s"%sleep_time)
                        time.sleep( sleep_time )
                else:
                    time.sleep( int( configuration['run-time'] ) )
            else:
                input("\nPress Enter to shutdown...")

            self.on_test_end(services, configuration)

        except Exception as err:
            die("Caught error during performance test:\n%s" % self._format_traceback(sys.exc_info(), err))

        finally:
            self.on_services_stopped(configuration)
            stop_stack.callFunctions()
            self._zip_logfiles(configuration['log-folder'], configuration['log-zip-file'])



    # HELPER FUNCTIONS
    def _delete_folders(self, *folders):
        """ delete folders if they exist """
        for folder in folders:
            if os.path.exists(folder):
                logger.debug("Deleting folder " + folder)
                shutil.rmtree(folder)

    def dump_statistics(self, filename, *mBean_pair):
        """ Dumps mbean statistics to file (through jolokia)"""
        logger.info("Dumping performance statistics to file %s" % filename)
        mbd = MBeanDumper(filename)

        mbd.dump(*mBean_pair)

    def plot_statistics(self, config_file, main_plot=None):
        """ plots statistics using the performace-report tool"""
        logger.info("Plotting performance statistics")
        performance_plotter.plot(config_file, main_plot=main_plot)

    def _save_service_logfiles(self, service, name, logfolder):
        """ Saves service logfiles """
        for logfile in service.get_logfiles():
            self._save_logfile(logfile, logfolder, prefix=name + "_")

    def _save_logfile(self, logfile, logfolder, prefix=None):
        """ Saves the logfile """
        dest = os.path.join(logfolder, os.path.basename(logfile))
        if prefix is not None:
            dest = os.path.join(logfolder, prefix + os.path.basename(logfile))

        shutil.copy(logfile, dest)

    def _zip_logfiles(self, logfolder, logzipfile):

        logger.info("Zipping log files")
        zfile = zipfile.ZipFile( os.path.abspath( logzipfile ), 'w', zipfile.ZIP_DEFLATED )
        for f in os.listdir( logfolder ):
            zfile.write( os.path.join(logfolder, f), f )
        zfile.close()

    def _format_traceback(self, exc_info, error):
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

    def fetch(self, resource):
            return os.path.abspath(os.path.join(self.configuration['resource-folder'], resource))

    def extractFileInWar(self, war_path, file_path):
        cur_dir = os.getcwd()
        basedir = os.path.dirname(war_path)
        os.chdir(basedir)

        cmd = "unzip -jo %s %s " % (war_path, file_path)
        (stdout, stderr) = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        logger.debug( "unzip output %s"%stdout+stderr)
        path = os.path.abspath(os.path.basename(file_path))
        if not os.path.isfile(path):
            die("unzip failed: could not find expected file %s after operation."%path)
        os.chdir(cur_dir)
        return path

    def runCmd(self, cmd):
        logger.debug("running cmd: %s" % cmd)
        (stdout, stderr) = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, executable="/bin/bash").communicate()
        logger.debug( "cmd output %s"%stdout+stderr)
        return stdout

    def _setup_logger(self, verbose=False):
            """ Sets up logger instance"""
            logging.basicConfig(level=logging.DEBUG,
                                format="%(asctime)s %(levelname)s %(message)s",
                                filename='run_perf_test.log',
                                filemode='w')
            logger = logging.getLogger('')
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            if verbose:
                ch.setLevel(logging.DEBUG)
            logger.addHandler(ch)


