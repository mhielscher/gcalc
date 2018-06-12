#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Usage: gcalc [options] [query]

Running without arguments will start interactive mode. Specifying an initial
query without the -i option will evaluate only that query.

Options:
  -h    show this help message and exit
  -i    run in interactive mode (even with an initial query)
"""

# Import the "lighter" modules
import os
import readline
import atexit
import sys
import json
import re
import threading
import time


## Load the heavy modules in the background after the prompt comes up
requests = None
lxml = None
BeautifulSoup = None
def import_heavies():
    global requests, lxml, BeautifulSoup
    import requests
    import lxml
    from bs4 import BeautifulSoup
th = threading.Timer(0, import_heavies)
th.start()


__VERSION__ = "2018.4.29"

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

    while requests == None: # Wait for requests to load
        time.sleep(0.1)
    r = requests.get(url, params=data, headers={'User-Agent': USER_AGENT})
    if r.status_code != 200:
        return "Error: HTTP status %d" % r.status_code

    s = r.text

    # Replace obfuscated escape sequence with the proper character
    if os.environ['LANG'].lower().find('utf') != -1:
        s = s.replace(u'\\u0026#215;', u'×')
    else:
        s = s.replace(u'\\u0026#215;', u'x')

    while BeautifulSoup == None: # Wait for BeautifulSoup (with lxml) to load
        time.sleep(0.1)
    page = BeautifulSoup(s, "lxml")

    # Most calculations:
    if page.find("div", "vk_bk") != None:
        # Currency conversion
        if page.find("span", id="knowledge-currency__src-amount"):
            lhs = "{:s} {:s} = ".format(''.join(page.select("span#knowledge-currency__src-amount")[0].contents),
                                        ''.join(page.select("span#knowledge-currency__src-currency")[0].contents))
            rhs = "{:s} {:s}".format(''.join(page.select("span#knowledge-currency__tgt-amount")[0].contents),
                                     ''.join(page.select("span#knowledge-currency__tgt-currency")[0].contents))
        else:
            lhs = ''.join(str(t).strip() for t in page.find("div", "vk_gy").contents)
            rhs = ''.join(str(t).strip() for t in page.find("div", "dDoNo").contents)

    # ...deprecated?:
    elif page.find("span", "cwcot") != None:
        lhs = ''.join(str(t).strip() for t in page.find("span", "cwclet").contents)
        rhs = ''.join(str(t).strip() for t in page.find("span", "cwcot").contents)

    # Older unit conversion (probably unused now):
    elif page.find("input", id="ucw_lhs_d") != None:
        # This does not include unit names; not sure how to grab those
        lhs = page.find("input", id="ucw_lhs_d")['value'] + " ="
        rhs = page.find("input", id="ucw_rhs_d")['value']

    # New unit conversion with dropdowns:
    elif page.find("div", "vk_c") != None:
        # Return first hit if it exists, else dummy tag
        values = [e['value'] for e in page.select("div.vk_c input")]
        units = [e.text for e in page.select(".vk_c select option[selected]")][1:]
        lhs = "%s %s = " % (values[0], units[0])
        rhs = "%s %s" % (values[1], units[1])

    else:
        return "Error: Could not find answer on result page.\nQuery: {}\nDirect link: {}".format(q, r.url)

    
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

def parse_query_args(args):
    """Determine how to join or separate arguments into one or more initial queries."""
    if len(args) > 1 and ' ' in ''.join(args):
        for q in args:
            print(process_query(q.strip()))
    else:
        for q in re.split('[;\n]', ' '.join(args)):
            print (process_query(q.strip()))


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
            parse_query_args(sys.argv[2:])
    else:
        parse_query_args(sys.argv[1:])

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

    # Enter the interactive shell - end with 'quit', 'exit', or <EOF> (Ctrl-D)
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
        if inputline:
            print(process_query(inputline.strip()))

