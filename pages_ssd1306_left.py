#!/usr/bin/python.pydPiper
# coding: UTF-8

from __future__ import unicode_literals


# Page Definitions
# See Page Format.txt for instructions and examples on how to modify your display settings

# Load the fonts needed for this system
FONTS = {
	'small': { 'default':True, 'file':'latin1_5x8.fnt','size':(5,8) },
#	'large': { 'file':'BigFont_10x16.fnt', 'size':(10,16) },
	'large': { 'file':'Vintl01_10x16.fnt', 'size':(10,16) },
	'tiny': { 'file':'upperasciiwide_3x5_fixed.fnt', 'size':(5,5) },
}

TRUETYPE_FONTS = {
	'DejaVuSans28': { 'file':'DejaVuSans.ttf', 'size':28 },
}

IMAGES = {
	'progbar': {'file':'progressbar_80x8.png' },
	'splash': {'file':'pydPiper_fixed_splash.png' }
}

# Load the Widgets that will be used to produce the display pages
WIDGETS = {
	'splash': { 'type':'text', 'format':'DCAudio\nStreamer', 'font':'large' },
	'volume': { 'type':'text', 'format':'Volume: {0}', 'variables':['volume'], 'font':'small', 'just':'left', 'size':(60,8), 'varwidth':True },
	'volumelarge': { 'type':'text', 'format':'Volume: {0}', 'variables':['volume'], 'font':'large', 'just':'left', 'varwidth':True },
	'volumebar': { 'type':'progressbar', 'value':'volume', 'rangeval':(0,100), 'size':(120,8) },
	'samplerate': { 'type':'text', 'format':'{0}', 'variables':['samplerate'], 'font':'small', 'just':'center','varwidth':True},
	'bitdepth': { 'type':'text', 'format':'{0}', 'variables':['bitdepth'], 'font':'small', 'just':'center','varwidth':True},
	'time': { 'type':'text', 'format':'{0}', 'variables':['time'], 'font':'large', 'just':'right', 'varwidth':True, 'size':(45,16) },
	'playstopstatus': { 'type':'text', 'format':'{0}', 'variables':['state|select+play+\ue000 Play+stop+\ue001 Stop'], 'font':'large', 'just':'left', 'size':(60,16) },
	'randomstatus': { 'type':'text', 'format':'{0}', 'variables':['random_onoff|select+On+\ue002+Off+\u0020'], 'font':'large', 'just':'left', 'size':(10,16) },
	'nowplaying': { 'type':'text', 'format':'{0}', 'variables':['actPlayer|upper'], 'font':'small', 'varwidth':True},
}

# Assemble the widgets into canvases.  Only needed if you need to combine multiple widgets together so you can produce effects on them as a group.
CANVASES = {
	'left_panel_normal': { 'widgets': [ ('nowplaying',1,0), ('volume',1,47), ('volumebar',1,56), ('playstopstatus',74,0), ('randomstatus',115,18) ], 'size':(128,64) },
}

# Place the canvases into sequences to display when their condition is met
# More than one sequence can be active at the same time to allow for alert messages
# You are allowed to include a widget in the sequence without placing it on a canvas

# Note about Conditionals
# Conditionals must evaluate to a True or False resulting
# To access system variables, refer to them within the db dictionary (e.g. db['title'])
# To access the most recent previous state of a variable, refer to them within the dbp dictionary (e.g. dbp['title'])
SEQUENCES = [
	{       'name': 'seqSplash', 
		'canvases': [ { 'name':'splash', 'duration':30 } ], 
		'conditional':"db['state']=='starting'"
	},
	{
		'name':'seqNormal',
		'coordinates':(0,0),
		'canvases': [ { 'name':'left_panel_normal', 'duration':99999,'conditional':"db['outside_conditions']=='No data'" } ],
		'conditional':"not db['state']=='starting'"
	},
]
