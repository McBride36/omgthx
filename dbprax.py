from tinydb import TinyDB, Query
import json


    #db.insert_multiple(json.load(f)
tellsdb = TinyDB('reprap.json')
#with open(newfile, 'w') as outfile, open(oldfile, 'r', encoding='utf-8') as infile:
with open('tell.json', encoding='utf-8') as t, open('factoids.json', encoding='utf-8')as f, open('factoid_history.json', encoding='utf-8')as fh, open('seen.json', encoding='utf-8') as s:
    factoids = tellsdb.table('factoids')
    factoids.insert_multiple(json.load(f, encoding='utf-8'))
    factoids_history = tellsdb.table('factoids_history')
    factoids_history.insert_multiple(json.load(fh, encoding='utf-8'))
    seen = tellsdb.table('seen')
    seen.insert_multiple(json.load(s, encoding='utf-8'))
    tell = tellsdb.table('tell')
    tell.insert_multiple(json.load(t, encoding='utf-8'))
