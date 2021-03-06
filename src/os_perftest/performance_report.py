#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`os_perftest.performance_report` -- report generator
=========================================================
"""
import os
import random
import shutil
import base64
import urllib.request, urllib.parse, urllib.error
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates

logger = logging.getLogger("dbc." + __name__)

color_map = { "b": "#0000FF",
              "r": "#FF0000",
              "g": "#00FF00",
              "c": "#00FFFF",
              "y": "#FFFF00",
              "k": "#000000",
              "m": "#FF00FF",
              'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aqua': '#00ffff', 'aquamarine': '#7fffd4',
              'azure': '#f0ffff', 'beige': '#f5f5dc', 'bisque': '#ffe4c4', 'black': '#000000',
              'blanchedalmond': '#ffebcd', 'blue': '#0000ff', 'blueviolet': '#8a2be2', 'brown': '#a52a2a',
              'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00', 'chocolate': '#d2691e',
              'coral': '#ff7f50', 'cornflowerblue': '#6495ed', 'cornsilk': '#fff8dc', 'crimson': '#dc143c',
              'cyan': '#00ffff', 'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b',
              'darkgray': '#a9a9a9', 'darkgreen': '#006400', 'darkgrey': '#a9a9a9', 'darkkhaki': '#bdb76b',
              'darkmagenta': '#8b008b', 'darkolivegreen': '#556b2f', 'darkorange': '#ff8c00', 'darkorchid': '#9932cc',
              'darkred': '#8b0000', 'darksalmon': '#e9967a', 'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b',
              'darkslategray': '#2f4f4f', 'darkslategrey': '#2f4f4f', 'darkturquoise': '#00ced1', 'darkviolet': '#9400d3',
              'deeppink': '#ff1493', 'deepskyblue': '#00bfff', 'dimgray': '#696969', 'dimgrey': '#696969',
              'dodgerblue': '#1e90ff', 'firebrick': '#b22222', 'floralwhite': '#fffaf0', 'forestgreen': '#228b22',
              'fuchsia': '#ff00ff', 'gainsboro': '#dcdcdc', 'ghostwhite': '#f8f8ff', 'gold': '#ffd700',
              'goldenrod': '#daa520', 'gray': '#808080', 'grey': '#808080', 'green': '#008000',
              'greenyellow': '#adff2f', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4', 'indianred': '#cd5c5c',
              'indigo': '#4b0082', 'ivory': '#fffff0', 'khaki': '#f0e68c', 'lavender': '#e6e6fa',
              'lavenderblush': '#fff0f5', 'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6',
              'lightcoral': '#f08080', 'lightcyan': '#e0ffff', 'lightgoldenrodyellow': '#fafad2', 'lightgray': '#d3d3d3',
              'lightgreen': '#90ee90', 'lightgrey': '#d3d3d3', 'lightpink': '#ffb6c1', 'lightsalmon': '#ffa07a',
              'lightseagreen': '#20b2aa', 'lightskyblue': '#87cefa', 'lightslategray': '#778899', 'lightslategrey': '#778899',
              'lightsteelblue': '#b0c4de', 'lightyellow': '#ffffe0', 'lime': '#00ff00', 'limegreen': '#32cd32',
              'linen': '#faf0e6', 'magenta': '#ff00ff', 'maroon': '#800000', 'mediumaquamarine': '#66cdaa',
              'mediumblue': '#0000cd', 'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db', 'mediumseagreen': '#3cb371',
              'mediumslateblue': '#7b68ee', 'mediumspringgreen': '#00fa9a', 'mediumturquoise': '#48d1cc', 'mediumvioletred': '#c71585',
              'midnightblue': '#191970', 'mintcream': '#f5fffa', 'mistyrose': '#ffe4e1', 'moccasin': '#ffe4b5',
              'navajowhite': '#ffdead', 'navy': '#000080', 'oldlace': '#fdf5e6', 'olive': '#808000',
              'olivedrab': '#6b8e23', 'orange': '#ffa500', 'orangered': '#ff4500', 'orchid': '#da70d6',
              'palegoldenrod': '#eee8aa', 'palegreen': '#98fb98', 'paleturquoise': '#afeeee', 'palevioletred': '#db7093',
              'papayawhip': '#ffefd5', 'peachpuff': '#ffdab9', 'peru': '#cd853f', 'pink': '#ffc0cb',
              'plum': '#dda0dd', 'powderblue': '#b0e0e6', 'purple': '#800080', 'red': '#ff0000',
              'rosybrown': '#bc8f8f', 'royalblue': '#4169e1', 'saddlebrown': '#8b4513', 'salmon': '#fa8072',
              'sandybrown': '#f4a460', 'seagreen': '#2e8b57', 'seashell': '#fff5ee', 'sienna': '#a0522d',
              'silver': '#c0c0c0', 'skyblue': '#87ceeb', 'slateblue': '#6a5acd', 'slategray': '#708090',
              'slategrey': '#708090', 'snow': '#fffafa', 'springgreen': '#00ff7f', 'steelblue': '#4682b4',
              'tan': '#d2b48c', 'teal': '#008080', 'thistle': '#d8bfd8', 'tomato': '#ff6347',
              'turquoise': '#40e0d0', 'violet': '#ee82ee', 'wheat': '#f5deb3', 'white': '#ffffff',
              'whitesmoke': '#f5f5f5', 'yellow': '#ffff00', 'yellowgreen': '#9acd32' }


class PerformanceReport( object ):

    def __init__( self, output_dir ):

        self.output_dir = os.path.abspath( output_dir )
        if os.path.exists( self.output_dir ):
            shutil.rmtree( self.output_dir )
        os.mkdir( self.output_dir )

        self.figs = []

    def plot_data( self, plot_name, description, unit, dates, *data_list ):

        tlen = len( dates )
        logger.debug("Plot data plot_name='%s', description='%s', unit=%s, dates=%s", plot_name, description, unit, tlen)
        fixed_tick_spacing = True


        #logger.debug("Plot data has %s records", tlen)

        for color, legend, lst, precision in data_list:
            if len( lst ) != tlen:
                raise RuntimeError( "mismatch in length of timestamp/data lists, %s != %s"%(len(lst), tlen) )

        fig = plt.figure()
        ax = fig.add_subplot(111)


        x_axis_ticks = None

        if fixed_tick_spacing:
            x_axis_ticks = list(range(tlen))
            def tick_format(a, b):
                if dates[int(a)] == datetime.datetime.fromtimestamp(0):
                    return ""
                else:
                    return dates[int(a)].strftime("%d-%m-%Y")
            ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(tick_format))
            ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(x_axis_ticks[0::6]))
        else:
            x_axis_ticks = dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())


        ax.set_xlim(x_axis_ticks[0], x_axis_ticks[-1])
        #ax.set_ylim( min( map( min, map( lambda x: x[2], data_list ) ) ) -2,
        #             max( map( max, map( lambda x: x[2], data_list ) ) ) +2 )
        ax.set_ylim( 0,
                     max( list(map( max, [x[2] for x in data_list] )) ) *1.1 )

        ax.grid( True )

        plot_legend = []

        for color, legend, lst, precision in data_list:

            plot_legend.append( (color_map[color], legend, lst[ -1 ], precision ) )
            plt.plot( x_axis_ticks, lst, color=color, aa=True, lw=1 )

        fig.autofmt_xdate()
        fname = os.path.join( self.output_dir, plot_name + '.png' )
        fname_small = os.path.join( self.output_dir, plot_name + '-small.png' )
        plt.ylabel( unit )
        plt.savefig( fname, dpi=150, bbox_inches='tight' )
        plt.savefig( fname_small, dpi=50, bbox_inches='tight' )
        plt.close()

        self.figs.append( { 'filename': fname, 'smallfilename': fname_small, 'plotname': plot_name, 'description': description, 'legend': plot_legend } )

    def create_report( self, filename='index.html', plot_name=None, legend_timing=True ):
        """
        if plot_name is supplied, the specific plot is also saved as a png file called 'main.png'
        """
        logger.debug("Create report filename='%s', plot_name='%s', legend_timing=%s", filename, plot_name, legend_timing)


        fh = open( os.path.join( self.output_dir, filename ), 'w' )

        for fig in self.figs:
            figname = os.path.basename( fig['filename'] )
            figname_small = os.path.basename( fig['smallfilename'] )
            fig_url = urllib.parse.quote( figname )
            fig_small_url = urllib.parse.quote( figname_small )
            plotname = fig['plotname']
            legend = fig['legend']
            description = fig['description']

            subname = os.path.splitext(figname)[0] + ".html"


            fh.write( "<p>\n")
            fh.write( "<h2>%s</h2>\n"%plotname )
            fh.write( "<b>Description: %s</b>\n"%description )
            fh.write( "<br>\n" )
            #fh.write( '<a href="%s"><img src="%s" alt="%s"></a>\n'%( fig_url, fig_small_url, plotname ) )
            fh.write( '<a href="%s"><img src="%s" alt="%s"></a>\n'%( subname, fig_small_url, plotname ) )
            if legend != []:
                fh.write( self._create_legend( legend, legend_timing ) )

            fh.write( "</p>\n")

            self._create_subreport( subname, figname, plotname, description, legend )

            if plotname == plot_name:
                shutil.copyfile( fig['filename'], os.path.join( self.output_dir, "main.png" ) )
                shutil.copyfile( fig['smallfilename'], os.path.join( self.output_dir, "main-small.png" ) )


    def _create_subreport( self, filename, image_name, plotname, description, legend_lst ):

        logger.debug("Create report filename='%s', image_name='%s', plot_name='%s', description='%s', legend_timing=%s", filename, image_name, plotname, description, legend_lst)
        fig_url = urllib.parse.quote( image_name )

        fh = open( os.path.join( self.output_dir, filename ), 'w' )
        fh.write( "<h2>%s</h2>\n"%plotname )
        fh.write( "<b>Description: %s</b>\n"%description )
        fh.write( "<br>\n" )
        fh.write( '<img src="%s" alt="%s">\n'%( fig_url, plotname ) )
        if legend_lst != []:
            fh.write( self._create_legend( legend_lst ) )


    def _create_legend( self, legend_lst, legend_timing=True ):

        legend_str = '<table border="0" style="margin-left:120px;">\n'
        legend_str += '<caption align="left"><em>Legend:&nbsp;&nbsp;&nbsp;&nbsp;</em></caption>\n'
        for legend in legend_lst:
            if legend_timing:
                legend_str += '<tr><td><font color="%s">&#9632;</font></td><td>%s:</td><td align=right>%.*f</td></tr>\n'%( legend[0], legend[1], legend[3], legend[2] )

            else:
                legend_str += '<tr><td><font color="%s">&#9632;</font></td><td>%s</td></tr>\n'%( legend[0], legend[1] )
                
        legend_str += "</table>\n"
        return legend_str


def gen_dates( num_of_dates, latest_date=None ):

    if latest_date == None:
        latest_date = datetime.datetime.now()

    dates = [latest_date - datetime.timedelta( ( num_of_dates -1 ))]

    while dates[-1] < latest_date:
        dates.append( dates[-1] + datetime.timedelta( 1 ) )
    return dates
