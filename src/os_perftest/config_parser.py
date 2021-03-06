#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`os_perftest.performance_config_parser` -- config parser
=============================================================
"""
from configobj import ConfigObj
import os_perftest.performance_dumper as dumper
import datetime

class ConfigParseError(Exception):
    pass

def parse_config(config_file):
    config = ConfigObj(config_file)
    config = validate_config(config)
    
    pd = dumper.MBeanDumper(config["main"]["datafile"])
    dump = pd._read_dump()
    
    graphs = []
    for graph in [x for x in list(config.keys()) if x != "main"]:
        graphvalues = { "name": graph, 
                        "description": config[graph]["description"],
                        "unit": config[graph]["unit"]}
        lines = []
        timestamps = []
        for line in [x for x in list(config[graph].keys()) if x != "description" and x != "unit"]:
            current = config[graph][line]

            linevalues = [current["color"], line]

            ycoords = pd.read_values_from_dump_new(dump, current["jolokiaurl"], current["mbean"], current["yCoordPath"])

            if current["precision"] == 0:
                ycoords = list(map(int, ycoords))
            
            linevalues.append(ycoords)
            linevalues.append(current["precision"])
            lines.append(linevalues)

            current_timestamps = pd.read_values_from_dump_new(dump, current["jolokiaurl"], current["mbean"], current["timestampPath"])
            if not timestamps:
                timestamps = current_timestamps
            else:
                for idx, val in enumerate(current_timestamps):
                    if timestamps[idx] == 0:
                        timestamps[idx] = val

        timestamps = list(map(datetime.datetime.fromtimestamp, timestamps))
        
        graphvalues["lines"] = lines
        
        graphvalues["timestamps"] = timestamps
        
        graphs.append(graphvalues)

    return graphs  

def validate_config(config):
    if "main" not in config or "datafile" not in config["main"]:
        raise ConfigParseError("Could not find 'main' entry in datafile")
    
    for graph in [x for x in list(config.keys()) if x != "main"]:

        if "unit" not in list(config[graph].keys()):
            raise ConfigParseError("Could not find unit in '%s'" % graph)
        if "description" not in list(config[graph].keys()):
            config[graph]["description"] = ""
        
        for line in [x for x in list(config[graph].keys()) if x != "description" and x != "unit"]:
            if "precision" not in config[graph][line]:
                config[graph][line]["precision"] = 0
            config[graph][line]["precision"] = int(config[graph][line]["precision"])
            
            if "timestampPath" not in config[graph][line]:
                config[graph][line]["timestampPath"] = "/timestamp"
                
    return config
