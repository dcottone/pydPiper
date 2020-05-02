#!/usr/bin/python
# coding: UTF-8

# musicdata service to read from MPD
# Written by: Ron Ritchey
from __future__ import unicode_literals

import json, mpd, threading, logging, Queue, time, sys, getopt
import musicdata

class musicdata_moode(musicdata.musicdata_mpd):
    def __init__(self, q, server=u'localhost', port=6600, pwd=u''):
        super(q,server,port,pwd)


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
			if start+120 < time.time():
				break;
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
