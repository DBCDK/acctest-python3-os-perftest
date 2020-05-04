#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`os_perftest.performance_dumper` -- mbean dumper (via jolokia)
===================================================================
"""
import urllib.request, urllib.error, urllib.parse
import logging
import datetime
import os
import json
import sys


class NullHandler( logging.Handler ):
    """ Nullhandler for logging.
    """

    def emit( self, record ):
        pass

### define logger
logger = logging.getLogger( "dbc." + __name__ )
logger.addHandler( NullHandler() )


class JolokiaConnector( object ):
    """
    Jolokia connector object designed for jmx communication.
    This is a copy of the class found in os_python.jolokia
    """

    def __init__( self, url ):
        self.url = url

    def list( self ):
        """
        """
        return self._request( "/".join( [self.url, 'list'] ) )

    def read( self, mBean, attribute=None, inner_path=None ):
        """
        """
        escape_map = { "/": "!/",
                        "!": "!!",
                        "(": "!(",
                        "[": "%5B",
                        "]": "%5D",
                        " ": "%20" }

        for entry in escape_map.items():
            mBean = mBean.replace( entry[0], entry[1] )

        url_lst = [ self.url, 'read', mBean ]
        if attribute != None:
            url_lst.append( attribute )
        request_url = "/".join( url_lst )
        if inner_path:
            request_url = "/".join( [ request_url, inner_path ] )
        request_url += "?ignoreErrors=true"

        return self._request( request_url )

    def _request( self, url, latency=30 ):
        """ Retrieves content from url.
        """

        logger.debug( "Requesting jolokia service with url: %s (latency=%s senconds)"%( url, latency ) )
        endtime = datetime.datetime.now() + datetime.timedelta( 0, latency )

        response = None
        while response == None:
            try:
                response = urllib.request.urlopen( url )
                response_str = response.read()
            except Exception as e:
                if datetime.datetime.now() > endtime:
                    err_msg = "Could not retrieve response in %s seconds. Latest error mesg %s"%( latency, e )
                    logger.error( err_msg )
                    raise e

        result = json.loads( response_str )
        status = result['status']
        if status != 200:
            err_msg = "Could not retrieve response from Jolokia App: error Code: %s"%status
            if status == 400 or status == 404:
                logger.warn( err_msg )
                logger.warn( "Original Response %s"%result )
            else:
                logger.error( err_msg )
                logger.error( "Original Response %s"%result )
                raise RuntimeError( err_msg )

        return result


class MBeanDumper( object ):

    def __init__( self, dump_file ):
        """ Initializes mBean dumper
        """
        self.dump_file = dump_file

    def dump( self, *mBean_pair, **kwargs):

        # Max history 70 plots. Older data will be truncated
        count = kwargs.get('count', 70);

        full_dump = self._read_dump()
        entry = self._dump_mBeans( *mBean_pair )
        full_dump = full_dump[-count:]
        full_dump.append( entry )
        self._write_dump( full_dump )

    def read_values( self, entry, path ):
        """ Constructs list of values found at path for the specific entry
        """
        dump = self._read_dump()

        return self.read_values_from_dump( dump, entry, path )

    def read_values_from_dump( self, dump, entry, path, id=None ):
        """ Constructs list of values found at path for the specific entry
        """
        if len( dump ) < 1:
            print("No entries in dump")

        entries = []
        for e in dump:
            entries += list(e.keys())

        entries = list(set(entries))

        if not entry in entries:
            print("Could not find %s in entries"%entry)

        values = []

        path = [str( x ) for x in path.split( "/" )]
        path.insert(0, str( entry ) )
        
        if id:
            path.insert(1, str( id ) )
        
        for entry in dump:

            self.val = 0
            self._walk( entry, tuple( path ) ),
            values.append( self.val )

        return values

    def read_values_from_dump_new( self, dump, entry, mbean, path):
        """ Constructs list of values found at path for the specific entry
        """
        if len( dump ) < 1:
            print("No entries in dump")

        entries = []
        for e in dump:
            entries += list(e.keys())

        entries = list(set(entries))
        
        if not entry in entries:
            print("Could not find %s in entries"%entry)

        values = []
        
        if "/" is path[0:1]:
            path = path[1:]

        path = [str( x ) for x in path.split( "/" )]
        path.insert(0, str( entry ) )
        path.insert(1, str( mbean ) )
        
        for entry in dump:

            self.val = 0
            self._walk( entry, tuple( path ) ),
            values.append( self.val )
        
        return values
    
    def _dump_mBeans( self, *mBean_pair ):
        """
        a mBean pair consists of a jolokia url where the mbeanserver is exposed, and the name of a mBean server to dump
        """

        entry = {}

        for pair in mBean_pair:
            if pair[1] not in entry:
                entry[pair[1]] = {}
            logger.info( "Requesting jolokia with url %s"%pair[0] )
            con = JolokiaConnector( pair[0] )
            keys = list(con.list()['value'][pair[1]].keys())
            for key in keys:
                entry[pair[1]][key] = con.read( pair[1] + ":" + key)

        return entry

    def _read_dump( self ):
        """ reads dump from file
        """
        dump = "[]"
        if os.path.exists( self.dump_file ):
            fh = open( self.dump_file )
            content = fh.read()
            fh.close()
            if content.strip() != "":
                dump = content

        return json.loads( dump )

    def _write_dump( self, dump ):
        """ Writes dump to file
        """
        fh = open( self.dump_file, 'w' )
        fh.write( json.dumps( dump, indent=4 ) )
        fh.close()

    def _walk( self, dikt, target_path, path=() ):

        for key in dikt:
            if path + ( key, ) == target_path:
                self.val = dikt[key]
            elif type( dikt[key] ) != dict:
                pass
            else:
                self._walk( dikt[key], target_path, path + ( key, ) )

if __name__ == '__main__':

    ### Logger
    logging.basicConfig( level = logging.DEBUG,
                         filename = 'performance-dumper.log',
                         filemode = 'w' )
    logger = logging.getLogger( '' )
    ch = logging.StreamHandler()
    ch.setLevel( logging.DEBUG )
    #if options.verbose:
    #    ch.setLevel( logging.DEBUG )
    logger.addHandler( ch )

    commands = ['dump', 'read']

    if len( sys.argv ) <2:

        sys.exit( "Please provide a command" )

    if sys.argv[1] not in commands:
        sys.exit( "Unknown command %s"%sys.argv[1] )

    if len( sys.argv ) < 3:
        sys.exit( "Please supply dump file" )

    mbd = MBeanDumper( sys.argv[2] )

    if sys.argv[1] == 'dump':
        mBean_pairs = [tuple( x.split( '=', 1 ) ) for x in sys.argv[3:]]
        mbd.dump( *mBean_pairs )

    else: # read
        read_pairs = [tuple( x.split( '=', 1 ) ) for x in sys.argv[3:]]
        for pair in read_pairs:
            print(pair[0] + " = ", mbd.read_values( *pair ))

#mbd = MBeanDumper( 'foo.txt' )

# print mbd.dump( ( "http://uqbar:7777/jolokia", "AddiService" ),
#                 ( "http://uqbar:7778/jolokia", "FieldSearchLucene" ) )

#print mbd.read_values( "AddiService", "name=RequestTiming,type=AddJob" )
#print mbd.read_values( "AddiService", "name=RequestTiming,type=AddJob/value/Count" )
