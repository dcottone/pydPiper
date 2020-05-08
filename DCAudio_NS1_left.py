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
	'GraphikBold28': { 'file':'/home/pi/pydPiper/fonts/GraphikBold.otf', 'size':28 },
	'GraphikThin28': { 'file':'/home/pi/pydPiper/fonts/GraphikThin.otf', 'size':28 },
    'GraphikSemibold20': { 'file':'/home/pi/pydPiper/fonts/GraphikSemibold.otf', 'size':20 },
}

IMAGES = {
	'progbar': {'file':'progressbar_80x8.png' },
	'splash': {'file':'pydPiper_fixed_splash.png' }
}

# Load the Widgets that will be used to produce the display pages
WIDGETS = {
	'splashDCaudio': { 'type':'ttext', 'format':'DCaudio', 'font':'GraphikBold28','just':'center','varwidth':True, 'size':(128,28) },
	'splashStreamer': { 'type':'ttext', 'format':'Streamer', 'font':'GraphikThin28','just':'center','varwidth':True, 'size':(128,28) },
	'artist': { 'type':'ttext', 'format':'{0}', 'variables':['artist'], 'font':'GraphikSemibold20', 'just':'center', 'effect':('scroll','left',1,1,20,'onloop',3,128), 'size':(128,20)},
	'bitdepth': { 'type':'text', 'format':'{0}', 'variables':['bitdepth'], 'font':'small', 'just':'left','varwidth':True},
	'samplerate': { 'type':'text', 'format':'{0}', 'variables':['samplerate'], 'font':'small', 'just':'right','varwidth':True, 'size':(40,8)},
	'encoding': { 'type':'text', 'format':'{0}', 'variables':['encoding|upper'], 'font':'small', 'just':'right','varwidth':True, 'size':(40,8)},
	'stopStatus': { 'type':'ttext', 'format':'STOP', 'font':'GraphikThin28', 'varwidth':True, 'just':'center', 'size':(128,28) },
}

# Assemble the widgets into canvases.  Only needed if you need to combine multiple widgets together so you can produce effects on them as a group.
CANVASES = {
	'splashLogo': { 'widgets': [ ('splashDCaudio',0,0), ('splashStreamer',0,35) ], 'size':(128,64) },
	'playing': { 'widgets': [ ('artist',0,20) , ('bitdepth',0,56), ('encoding',88,0), ('samplerate',88,56)], 'size':(128,64) },
	'showstop': { 'widgets': [ ('stopStatus',0,18) ], 'size':(128,64) },
	'blank': { 'widgets': [], 'size':(128,64) },
}

# Place the canvases into sequences to display when their condition is met
# More than one sequence can be active at the same time to allow for alert messages
# You are allowed to include a widget in the sequence without placing it on a canvas

# Note about Conditionals
# Conditionals must evaluate to a True or False resulting
# To access system variables, refer to them within the db dictionary (e.g. db['title'])
# To access the most recent previous state of a variable, refer to them within the dbp dictionary (e.g. dbp['title'])
SEQUENCES = [
	{
		'name': 'seqSplash',
		'canvases': [ { 'name':'splashLogo', 'duration':30 } ],
		'conditional':"db['state']=='starting'"
	},
	{
		'name': 'seqPlay',
		'canvases': [
			{ 'name':'playing', 'duration':9999, 'conditional':'True' }
		],
		'conditional': "db['state']=='play'"
	},
	{
		'name': 'seqAnnounceStop',
		'canvases': [ 
			{ 'name':'showstop', 'duration':9999999} 
		],
		'conditional': "db['state']=='stop' or db['state']=='pause'"
	},
]
