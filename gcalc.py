#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import simplejson as json

error_codes = {
    "0": "No calculation identified.",
    "4": "Did not recognize input.",
    }

def process_query(q):
	"""Send the query, interpret the response, and return a composed string."""
	# Encode query, make request, read response
	url = "http://www.google.com/ig/calculator"
	data = [("hl", "en"), ("q", q)]
	postdata = urllib.urlencode(data)
	url = url+'?'+postdata
	f = urllib2.urlopen(url)
	r = f.read()
	# Apparently this is the encoding of the return?
	r = r.decode('cp1252')

	# Correct the invalid JSON
	r = r.replace('{', '{"')
	r = r.replace(': ', '":')
	r = r.replace(',', ', "')
	r = r.replace(u'\\x', u'\\u00')
	# Replace the nonbreaking space that python chokes on
	r = r.replace(u'\xa0', u',')
	# Replace obfuscated escape sequence with the proper character
	if os.environ['LANG'].lower().find('utf'):
	    r = r.replace(u'\\u0026#215;', u'×')
	else:
	    r = r.replace(u'\\u0026#215;', u'x')

	# Parse JSON
	jdata = json.loads(r)

	#print result
	if jdata['error'] != "":
		error = jdata['error']
		if error in error_codes.keys():
		    error = error_codes[error]
		return "Error: "+error
	else:
		lhs = jdata['lhs']
		rhs = jdata['rhs']
		sup_start = rhs.find("<sup>")
		if sup_start != -1:
			sup_end = rhs.find("</sup>")
			rhs = rhs[:sup_start] + "^" + rhs[sup_start+5:sup_end] + rhs[sup_end+6:]
		return lhs + " = " + rhs

interactive = False
initialquery = None
is_shell = sys.stdin.isatty()

# Read options, initial query, interactive mode
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

# Process query entered on the command line if it exists
if initialquery:
	print process_query(initialquery)

# Register the history file for the interactive shell
if interactive and is_shell:
	def save_history(histfile):
		readline.write_history_file(histfile)

	histfile = os.path.join(os.environ["HOME"], ".gcalc_history")
	try:
		readline.read_history_file(histfile)
	except IOError:
		pass

	atexit.register(save_history, histfile)

# Enter the interactive shell - end with 'quit' or 'exit'
while interactive:
	try:
		if is_shell:
			inputline = raw_input("; ")
		else:
			inputline = sys.stdin.readline()
	except EOFError:
		if is_shell: print ''
		sys.exit(0)
	if inputline == "exit" or inputline == "quit" or (not is_shell and inputline == ''):
		sys.exit(0)
	print process_query(inputline.strip())

