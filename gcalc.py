#!/usr/bin/python3
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
import requests
import json
import re
#from HTMLParser import HTMLParser

## TODO: load this in the background after the prompt comes up
from bs4 import BeautifulSoup

__VERSION__ = "2013.8.25"

#USER_AGENT = "gcalc/"+__VERSION__+" "+requests.utils.default_user_agent()
USER_AGENT = "gcalc/"+__VERSION__+" "+"Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36"

ERROR_CODES = {
    "0": "No calculation identified.",
    "4": "Did not recognize input.",
    }

# class MLStripper(HTMLParser):
#     def __init__(self):
#         self.reset()
#         self.fed = []
#     def handle_data(self, d):
#         self.fed.append(d)
#     def get_data(self):
#         return ''.join(self.fed)

# def strip_tags(html):
#     s = MLStripper()
#     s.feed(html)
#     return s.get_data()

def process_query(q):
    """Send the query, interpret the response, and return a composed string."""
    # Encode query, make request, read response
    # The iGoogle JSON-like interface is gone, so resort to screen-scraping.
    url = "http://www.google.com/search"
    data = {"hl": "en", "q": q}
    r = requests.get(url, params=data, headers={'User-Agent': USER_AGENT})
    if r.status_code != 200:
        return "Error: HTTP status %d" % r.status_code
    
    s = r.text
    
    # Replace obfuscated escape sequence with the proper character
    if os.environ['LANG'].lower().find('utf') != -1:
        s = s.replace(u'\\u0026#215;', u'×')
    else:
        s = s.replace(u'\\u0026#215;', u'x')

    page = BeautifulSoup(s, "lxml")
    # Calculation with operators
    if page.find("div", "vk_ans") != None:
        lhs = ''.join(t.strip() for t in page.find("div", "vk_gy").contents)
        rhs = ''.join(t.strip() for t in page.find("div", "vk_ans").contents)
    # ?
    elif page.find("span", "cwcot") != None:
        lhs = ''.join(t.strip() for t in page.find("span", "cwclet").contents)
        rhs = ''.join(t.strip() for t in page.find("span", "cwcot").contents)
    # ?
    elif page.find("input", id="ucw_lhs_d") != None:
        # This does not include units; not sure how to grab those
        lhs = page.find("input", id="ucw_lhs_d")['value'] + " ="
        rhs = page.find("input", id="ucw_rhs_d")['value']
    # Unit conversion
    elif page.find("div", "vk_c") != None:
        # Return first hit if it exists, else dummy tag
        lhs_value = next(iter(page.select("#_Aif input")), page.input)['value']
        lhs_unit = next(iter(page.select("#_Aif select option[selected]")), page.option).text
        lhs = "%s %s = " % (lhs_value, lhs_unit)
        rhs_value = next(iter(page.select("#_Cif input")), page.input)['value']
        rhs_unit = next(iter(page.select("#_Cif select option[selected]")), page.option).text
        rhs = "%s %s" % (rhs_value, rhs_unit)
    else:
        return "Error: Could not parse answer."
    
    # Translate fractions
    rhs = re.sub(r'<sup>(.*)</sup>&#8260;<sub>(.*)</sub>', r' \1/\2', rhs)
    # Translate exponents
    rhs = re.sub(r'<sup>(.*)</sup>', r'^\1', rhs)
    # Separate divs
    lhs = re.sub(r'</div>\s*', "</div>\n", lhs)
    rhs = re.sub(r'</div>\s*', "</div>\n", rhs)
    # Strip remaining HTML
    lhs = BeautifulSoup(lhs, "lxml").get_text()
    rhs = BeautifulSoup(rhs, "lxml").get_text()
    # Strip whitespace at start and end of lines
    lhs = re.sub(r'\s*\n\s*', "\n", lhs).strip()
    rhs = re.sub(r'\s*\n\s*', "\n", rhs).strip()
    return lhs + " " + rhs


if __name__ == '__main__':
    interactive = False
    initialquery = None
    is_shell = sys.stdin.isatty()

    # Read options, initial query, interactive mode
    if "-h" in sys.argv:
        print(__doc__)
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
        print(process_query(initialquery))

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
                inputline = input("; ")
            else:
                inputline = sys.stdin.readline()
        except EOFError:
            if is_shell:
                print('')
            sys.exit(0)
        if inputline == "exit" or inputline == "quit" or (not is_shell and inputline == ''):
            sys.exit(0)
        print(process_query(inputline.strip()))

