#!/usr/bin/python

"""gcalc.py: Command-line utility for Google Calculator."""

__author__ = "Matthew Hielscher"
__date__ = "2011-09-11"
__copyright__ = "Copyright 2011, Matthew Hielscher"
__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Matthew Hielscher"


import os
import readline
import atexit
import sys
import urllib
import urllib2
import json
import xml.sax.saxutils

def process_query(q):
	#encode query, make request, read response
	url = "http://www.google.com/ig/calculator"
	data = [("hl", "en"), ("q", q)]
	postdata = urllib.urlencode(data)
	url = url+'?'+postdata
	f = urllib2.urlopen(url)
	r = f.read()
	#print r

	#correct the invalid JSON
	r = r.replace('{', '{"')
	r = r.replace(': ', '":')
	r = r.replace(',', ', "')
	r = r.replace('\\x', '\\u00')
	#replace the nonbreaking space that python chokes on
	r = r.replace('\xa0', ',')
	#replace & escape sequence and unescape HTML
	r = r.replace('\\u0026', '&')
	r = xml.sax.saxutils.unescape(r, {'&#215;':'x'})
	#print r

	#parse JSON
	jdata = json.loads(r)

	#print result
	if jdata['error'] != "":
		return "Error: "+jdata['error']
	else:
		return jdata['lhs']+" = "+jdata['rhs']


interactive = False
initialquery = None

#read options, initial query, interactive mode
if len(sys.argv) < 2:
	interactive = True
elif sys.argv[1] == "-i":
	interactive = True
	if len(sys.argv) > 2:
		initialquery = sys.argv[2]
else:
	initialquery = sys.argv[1]

#process query entered on the command line if it exists
if initialquery:
	print process_query(initialquery)

#register the history file for the interactive shell
if interactive:
	def save_history(histfile):
		readline.write_history_file(histfile)

	histfile = os.path.join(os.environ["HOME"], ".gcalc_history")
	try:
		readline.read_history_file(histfile)
	except IOError:
		pass

	atexit.register(save_history, histfile)

#enter the (basic) interactive shell
# - end with 'quit' or 'exit'
while interactive:
	try:
		inputline = raw_input("; ")
	except EOFError:
		print ''
		sys.exit(0)
	if inputline == "exit" or inputline == "quit":
		sys.exit(0)
	print process_query(inputline)


"""
#Non-JSON parsing
r = r.strip("{} \n")
items = r.split(",")
rdata = {}
for i in items:
	label, value = i.split(": ")
	value = value.strip('"')
	rdata[label] = value
if rdata['error'] != "":
	print "Error: "+rdata['error']
else:
	print (rdata['lhs']+" = "+rdata['rhs']).replace('\xa0', ',')
"""
