#!/usr/bin/env python3

from requests import get
import re
import html.parser

r = get("http://bot.kthx.nl/bot/factoid")
last_page_pattern = r'Go to last page" href="/bot/factoid\?page=(\d+)"'
last_page_match = re.search(last_page_pattern, r.text)

lastpage = int(last_page_match.groups()[0])

factoid_pattern = r'<tr class="(even|odd)"><td class="subject">([^<]+)</td><td class="([\w]+)">([\w]+)</td><td class="statement">(.*?)</td>'

for page in range(1, lastpage):
    r = get("http://bot.kthx.nl/bot/factoid?page={}".format(page))
    matches = re.findall(factoid_pattern, r.text)

    for subject in matches:
        entry = u"{} {} {}".format(subject[1], subject[3], subject[4])
        print(html.parser.unescape(entry))