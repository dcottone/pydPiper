#!/usr/bin/python
# coding: UTF-8

# musicdata service to read from MPD
# Written by: Ron Ritchey
from __future__ import unicode_literals

import json, mpd, threading, logging, Queue, time, sys, getopt, subprocess
import sources.musicdata_mpd

class musicdata_moode(musicdata_mpd.musicdata_mpd):

	def status(self):
		# Read musicplayer status and update musicdata
		localMusicBase = "/var/lib/mpd/music/"
		bitdepth = u""
		samplerate = u""
		chnum = 0

		try:
			status = self.dataclient.status()
			current_song = self.dataclient.currentsong()
			playlist_info = self.dataclient.playlistinfo()
		except:
			# Caught something else.  Report it and then inform calling function that the connection is bad
			e = sys.exc_info()[0]
			logging.debug(u"Caught {0} trying to get status".format(e))
			raise RuntimeError(u"Could not get status from MPD")


		state = status.get(u'state')
		if state != u"play":
			self.musicdata[u'state'] = u"stop"
		else:
			self.musicdata[u'state'] = u"play"

		# Update remaining variables
		self.musicdata[u'artist'] = current_song[u'artist'] if u'artist' in current_song else u""
		self.musicdata[u'title'] = current_song[u'title'] if u'title' in current_song else u""
		self.musicdata[u'album'] = current_song[u'album'] if u'album' in current_song else u""
		self.musicdata[u'volume'] = self.intn(status[u'volume']) if u'volume' in status else 0
		self.musicdata[u'repeat'] = bool(self.intn(status[u'repeat'])) if u'repeat' in status else False
		self.musicdata[u'random'] = bool(self.intn(status[u'random'])) if u'random' in status else False
		self.musicdata[u'single'] = bool(self.intn(status[u'single'])) if u'single' in status else False
		self.musicdata[u'uri'] = current_song[u'file'] if u'file' in current_song else u""


		# status['time'] is formatted as "current:duration" e.g. "24:243"
		# split time into current and duration
		temptime = status[u'time'] if u'time' in status else u'0:0'
		(self.musicdata[u'elapsed'], self.musicdata[u'length']) = temptime.split(u':')

		self.musicdata[u'elapsed'] = int(self.musicdata[u'elapsed'])
		self.musicdata[u'length'] = int(self.musicdata[u'length'])

		# for backwards compatibility
		self.musicdata[u'current'] = self.musicdata[u'elapsed']
		self.musicdata[u'duration'] = self.musicdata[u'length']

		self.musicdata[u'actPlayer'] = u"MPD"
		self.musicdata[u'musicdatasource'] = u"MPD"

		if self.musicdata[u'uri'].split(u':')[0] == u'http':
			encoding = u'stream'
			if len(self.musicdata[u'uri'].split(u'/')) >= 4:
				if self.musicdata[u'uri'].split(u'/')[3] == u'tidal':
					encoding = u'tidal'
					self.musicdata[u'musicdatasource'] = u"upnp"
		else:
			encoding = self.musicdata[u'uri'].split(u':')[0]
			if len(encoding) > 0:
				filepath = localMusicBase+encoding
				p = None
				p = subprocess.Popen(['mediainfo', '--Inform=Audio;%Format_Commercial%', filepath], stdout=subprocess.PIPE, stderr=None)
				mediainfoFormat = p.communicate()[0].strip().decode('utf-8')
				encoding = mediainfoFormat
				bitdepth = u'1bit'

		self.musicdata[u'encoding'] = encoding

		self.musicdata[u'bitrate'] = u"{0} kbps".format(status[u'bitrate']) if u'bitrate' in status else u""

		plp = self.musicdata[u'playlist_position'] = int(status[u'song'])+1 if u'song' in status else 0
		plc = self.musicdata[u'playlist_length'] = int(status[u'playlistlength']) if u'playlistlength' in status else 0

		# For Backwards compatibility
		self.musicdata[u'playlist_count'] = self.musicdata[u'playlist_length']

		# If playlist is length 1 and the song playing is from an http source it is streaming
		if self.musicdata[u'encoding'] == u'stream':
			self.musicdata[u'playlist_display'] = u"Radio"
			if not self.musicdata[u'artist']:
				self.musicdata[u'artist'] = current_song[u'name'] if u'name' in current_song else u""
		else:
				self.musicdata[u'playlist_display'] = u"{0}/{1}".format(self.musicdata[u'playlist_position'], self.musicdata[u'playlist_count'])

		audio = status[u'audio'] if u'audio' in status else None
		
		if self.musicdata[u'encoding']:
			tracktype = self.musicdata[u'encoding']
		else:
			tracktype = u"MPD"

		if audio is not None:
			audio = audio.split(u':')
			if len(audio) == 3:
				sample = round(float(audio[0])/1000,1)
			 	bits = audio[1]
				chnum = int(audio[2])
			 	if audio[2] == u'1':
					channels = u'Mono'
			 	elif audio[2] == u'2':
				 	channels = u'Stereo'
			 	elif int(audio[2]) > 2:
				 	channels = u'Multi'
			 	else:
				 	channels = u""

		 		tracktype = u"{0} {1} {2} bit {3} kHz".format(self.musicdata[u'encoding'], channels, bits, sample).strip()

				bitdepth = u"{0}bit".format(bits)
				samplerate = u"{0}kHz".format(sample)
		
		self.musicdata[u'tracktype'] = tracktype
		self.musicdata[u'bitdepth'] = bitdepth
		self.musicdata[u'samplerate'] = samplerate
		self.musicdata[u'channels'] = chnum

		# if duration is not available, then suppress its display
		if int(self.musicdata[u'length']) > 0:
			timepos = time.strftime(u"%-M:%S", time.gmtime(int(self.musicdata[u'elapsed']))) + u"/" + time.strftime(u"%-M:%S", time.gmtime(int(self.musicdata[u'length'])))
			remaining = time.strftime(u"%-M:%S", time.gmtime( int(self.musicdata[u'length']) - int(self.musicdata[u'elapsed']) ) )
		else:
			timepos = time.strftime("%-M:%S", time.gmtime(int(self.musicdata['elapsed'])))
			remaining = timepos

		self.musicdata[u'remaining'] = remaining.decode()
		self.musicdata[u'elapsed_formatted'] = timepos.decode()

		# For backwards compatibility
		self.musicdata[u'position'] = self.musicdata[u'elapsed_formatted']

		self.validatemusicvars(self.musicdata)


if __name__ == u'__main__':

	logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=u'musicdata_moode.log', level=logging.DEBUG)
	logging.getLogger().addHandler(logging.StreamHandler())

	# Suppress MPD libraries INFO messages
	loggingMPD = logging.getLogger(u"moode")
	loggingMPD.setLevel( logging.WARN )

	try:
		opts, args = getopt.getopt(sys.argv[1:],u"hs:p:w:",[u"server=",u"port=",u"pwd="])
	except getopt.GetoptError:
		print u'musicdata_moode.py -s <server> -p <port> -w <password>'
		sys.exit(2)

	# Set defaults
	server = u'localhost'
	port = 6600
	pwd= u''

	for opt, arg in opts:
		if opt == u'-h':
			print u'musicdata_moode.py -s <server> -p <port> -w <password>'
			sys.exit()
		elif opt in (u"-s", u"--server"):
			server = arg
		elif opt in (u"-p", u"--port"):
			port = arg
		elif opt in (u"-w", u"--pwd"):
			pwd = arg

	q = Queue.Queue()
	mdr = musicdata_moode(q, server, port, pwd)

	try:
		start = time.time()
		while True:
			if start+1200 < time.time():
				break
			try:
				item = q.get(timeout=1000)
				print u"+++++++++"
				for k,v in item.iteritems():
					print u"[{0}] '{1}' type {2}".format(k,v,type(v))
				print u"+++++++++"
				print
				q.task_done()
			except Queue.Empty:
				pass
	except KeyboardInterrupt:
		print u''
		pass

	print u"Exiting..."
