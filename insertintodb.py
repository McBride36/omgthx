import arrow

from tinydb import TinyDB, Query
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sql_declarative import Factoids, Seen, Factoid_history

reprapDB = TinyDB('reprap.json')
factoids = reprapDB.table('factoids')
factoids_history = reprapDB.table('factoids_history')
seentable = reprapDB.table('seen')
telltable = reprapDB.table('tell')
generalquery = Query()

engine = create_engine('sqlite:///reprap_database.db')

session = sessionmaker()
session.configure(bind=engine)
s = session()

# {"id":3030,"item":"JATMN","are":0,"value":"JAT.MN","nick":"JATMN","dateset":"2014-01-01 02:46:48","locked":null,"lastsync":null}
for element in factoids.all():
    element['dateset'] = arrow.get(element['dateset']).naive
    entry = Factoids(**element)
    s.add(entry)
s.commit()
print("factoids commited")

for element in factoids_history.all():
    if element['value'] is not None:
        element['dateset'] = arrow.get(element['dateset']).naive
        entry = Factoid_history(**element)
        s.add(entry)
s.commit()
print("factoid history commited")


for element in seentable.all():
    element['timestamp'] = arrow.get(element['timestamp']).naive
    entry = Seen(**element)
    s.add(entry)
s.commit()
print("seenTable commited")



