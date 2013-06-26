#!/usr/bin/python

"""Usage: gcalc [options] [query]

Running without arguments will start interactive mode. Specifying an initial
query without the -i option will evaluate only that query.

Options:
  -h    show this help message and exit
  -i    run in interactive mode (even with an initial query)
"""


import os
import readline
import atexit
import sys
import urllib
import urllib2
import json
import xml.sax.saxutils

def process_query(q):
	"""Send the query, interpret the response, and return a composed string."""
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
is_shell = sys.stdin.isatty()

#read options, initial query, interactive mode
if "-h" in sys.argv:
	print __doc__
	exit(0)
elif len(sys.argv) < 2:
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
if interactive and is_shell:
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
		if is_shell:
			inputline = raw_input("; ")
		else:
			inputline = sys.stdin.readline()
	except EOFError:
		if is_shell: print ''
		sys.exit(0)
	if not inputline.strip():
	    continue
	elif inputline == "exit" or inputline == "quit" or (not is_shell and inputline == ''):
		sys.exit(0)
	print process_query(inputline.strip())

